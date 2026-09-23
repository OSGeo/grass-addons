#!/usr/bin/env python3
"""
PRISMA L2D importer:
- Loads VNIR+SWIR PRISMA L2D data and builds a full 3D raster (r3) of reflectance (float32).
- Creates selected 3-band composites (RGB, CIR, SWIR_* or custom wavelengths) by nearest-band lookup.
- Sets region to match the transposed (E, N) raster layout and writes NULLs outside the valid footprint.
- Enhances colors via i.colors.enhance and assembles final composites with r.composite; temp bands are cleaned up.
Entry points:
  - import_prisma(input_path, output_name, composites=None, custom_wavelengths=None, strength_val=96)
  - run_import(options, flags)  # wrapper for module CLI
Requires: prisma_reader.{load_prisma_l2d, concatenate_hyperspectral}
"""

import os
import uuid
import shlex
from datetime import datetime, timezone
import numpy as np
import h5py
from pyproj import CRS, Transformer
import grass.script as gs
import grass.script.array as garray
from grass.pygrass.modules import Module

from hyper_meta import HyperMetadata
from prisma_reader import load_prisma_l2d, concatenate_hyperspectral

COMPOSITES = {
    "rgb": [660.0, 572.0, 478.0],
    "cir": [848.0, 660.0, 572.0],
    "swir_agriculture": [848.0, 1653.0, 660.0],
    "swir_geology": [2200.0, 848.0, 572.0],
}


# -------------------------- helpers --------------------------
def _require(cond, msg):
    if not cond:
        gs.fatal(msg)


def _resolve_he5(path_like):
    if os.path.isdir(path_like):
        for n in sorted(os.listdir(path_like)):
            if n.lower().endswith(".he5"):
                return os.path.join(path_like, n)
        gs.fatal("No .he5 file found in the provided folder.")
    return path_like


def _find_nearest_band_1based(target_nm, wavelengths_nm):
    wl = np.asarray(wavelengths_nm, dtype=np.float32)
    return int(np.argmin(np.abs(wl - float(target_nm)))) + 1  # 1-based


def _temp_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _to_float(value):
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _decode_text(value):
    if value is None:
        return None
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, (bytes, bytearray)):
        try:
            return value.decode("utf-8", errors="ignore")
        except Exception:
            return str(value)
    if isinstance(value, np.ndarray):
        if value.ndim == 0:
            return _decode_text(value.item())
        if value.dtype.kind in ("S", "U"):
            return [str(_decode_text(x)) for x in value.tolist()]
        return value.tolist()
    return str(value) if isinstance(value, (np.str_,)) else value


def _first_attr(attrs, keys):
    """Return first present non-empty attribute as (key, value)."""
    for key in keys:
        if key not in attrs:
            continue
        value = attrs.get(key)
        if value is None:
            continue
        decoded = _decode_text(value)
        if isinstance(decoded, str) and not decoded.strip():
            continue
        return key, value
    return None, None


def _to_iso_utc(text):
    if text is None:
        return None
    value = str(_decode_text(text)).strip()
    if not value:
        return None
    if value.endswith("Z"):
        return value
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return value
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _day_of_year(iso_text):
    if not iso_text:
        return None
    text = str(iso_text).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timetuple().tm_yday)


def _mean_dataset(h5obj, path):
    if path not in h5obj:
        return None
    arr = np.asarray(h5obj[path][()]).astype(np.float64, copy=False)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return None
    return float(np.nanmean(finite))


def _line_time_summary(arr):
    vals = np.asarray(arr).ravel()
    vals = vals[np.isfinite(vals)]
    if vals.size == 0:
        return None
    vals = np.sort(vals.astype(np.float64, copy=False))
    if vals.size > 1:
        diffs = np.diff(vals)
        diffs = diffs[np.isfinite(diffs)]
        step = float(np.nanmean(diffs)) if diffs.size else None
    else:
        step = None
    return {
        "count": int(vals.size),
        "min": float(vals[0]),
        "max": float(vals[-1]),
        "step": step,
    }


def _populate_prisma_extended_metadata(
    meta,
    he5_path,
    prod,
    wavelengths_meta,
    fwhm_meta,
    validity_meta,
):
    attrs = getattr(prod, "attrs", {}) or {}
    product_type = getattr(prod, "product_type", "L2D")

    swath_prefix = f"/HDFEOS/SWATHS/PRS_{product_type}_HCO"
    observing_path = f"{swath_prefix}/Geometric Fields/Observing_Angle"
    rel_azimuth_path = f"{swath_prefix}/Geometric Fields/Rel_Azimuth_Angle"
    time_path = f"{swath_prefix}/Geolocation Fields/Time"
    uncertainty_paths = (
        f"{swath_prefix}/Data Fields/VNIR_PIXEL_L2_ERR_MATRIX",
        f"{swath_prefix}/Data Fields/SWIR_PIXEL_L2_ERR_MATRIX",
        f"/HDFEOS/SWATHS/PRS_{product_type}_PCO/Data Fields/PIXEL_L2_ERR_MATRIX",
    )

    start_time_key, start_time_raw = _first_attr(
        attrs,
        (
            "Product_StartTime",
            "Acquisition_Start_Time",
        ),
    )
    end_time_key, end_time_raw = _first_attr(
        attrs,
        (
            "Product_StopTime",
            "Acquisition_Stop_Time",
        ),
    )
    sun_zenith_key, sun_zenith_raw = _first_attr(
        attrs,
        ("Sun_zenith_angle",),
    )
    sun_azimuth_key, sun_azimuth_raw = _first_attr(
        attrs,
        ("Sun_azimuth_angle",),
    )

    start_time = _to_iso_utc(start_time_raw)
    end_time = _to_iso_utc(end_time_raw)
    center_lat = _to_float(attrs.get("Product_center_lat"))
    center_lon = _to_float(attrs.get("Product_center_long"))
    sun_zenith = _to_float(sun_zenith_raw)
    sun_azimuth = _to_float(sun_azimuth_raw)

    observing_mean = None
    rel_azimuth_mean = None
    line_time = None
    uncertainty_present = False

    with h5py.File(he5_path, "r") as f:
        observing_mean = _mean_dataset(f, observing_path)
        rel_azimuth_mean = _mean_dataset(f, rel_azimuth_path)
        if time_path in f:
            line_time = _line_time_summary(f[time_path][()])
        uncertainty_present = any(p in f for p in uncertainty_paths)

    view_azimuth = None
    if sun_azimuth is not None and rel_azimuth_mean is not None:
        view_azimuth = float((sun_azimuth + rel_azimuth_mean) % 360.0)

    vmin = _to_float(attrs.get("L2ScaleVnirMin"))
    vmax = _to_float(attrs.get("L2ScaleVnirMax"))
    smin = _to_float(attrs.get("L2ScaleSwirMin"))
    smax = _to_float(attrs.get("L2ScaleSwirMax"))
    pmin = _to_float(attrs.get("L2ScalePanMin"))
    pmax = _to_float(attrs.get("L2ScalePanMax"))

    scale = {}
    if vmin is not None and vmax is not None:
        scale["vnir"] = (vmax - vmin) / 65535.0
    if smin is not None and smax is not None:
        scale["swir"] = (smax - smin) / 65535.0
    if pmin is not None and pmax is not None:
        scale["pan"] = (pmax - pmin) / 65535.0

    offset = {}
    if vmin is not None:
        offset["vnir"] = vmin
    if smin is not None:
        offset["swir"] = smin
    if pmin is not None:
        offset["pan"] = pmin

    cloud_pct = _to_float(attrs.get("Cloudy_pixels_percentage"))
    quality_atm = _decode_text(attrs.get("L2d_Quality_flags"))
    processing_dt = _to_iso_utc(attrs.get("Processing_Time"))
    processor_name = _decode_text(attrs.get("Processor_Name"))
    processor_version = _decode_text(attrs.get("Processor_Version"))
    l1_processor_version = _decode_text(attrs.get("L1_Processor_Version"))

    meta.set_extended_value("acquisition.start_time_utc", start_time)
    meta.set_extended_value("acquisition.end_time_utc", end_time)
    meta.set_extended_value("acquisition.center_latitude_deg", center_lat)
    meta.set_extended_value("acquisition.center_longitude_deg", center_lon)
    meta.set_extended_value("acquisition.day_of_year", _day_of_year(start_time))
    meta.set_extended_value("acquisition.line_time_summary", line_time)

    meta.set_extended_value("geometry.sun_zenith_deg", sun_zenith)
    meta.set_extended_value("geometry.sun_azimuth_deg", sun_azimuth)
    meta.set_extended_value("geometry.view_zenith_deg", observing_mean)
    meta.set_extended_value("geometry.view_azimuth_deg", view_azimuth)
    meta.set_extended_value("geometry.relative_azimuth_deg", rel_azimuth_mean)
    if product_type in ("L1", "L2C"):
        meta.set_extended_value("geometry.geocoding", "per_pixel_latlon_nearest")

    is_l1 = product_type == "L1"
    meta.set_extended_value(
        "radiometry.quantity", "toa_radiance" if is_l1 else "surface_reflectance"
    )
    meta.set_extended_value(
        "radiometry.units", "W/(m^2 sr um)" if is_l1 else "unitless"
    )
    if scale:
        meta.set_extended_value("radiometry.scale", scale)
    if offset:
        meta.set_extended_value("radiometry.offset", offset)
    if is_l1:
        scale_factor = {}
        for key, attr_name in (
            ("vnir", "ScaleFactor_Vnir"),
            ("swir", "ScaleFactor_Swir"),
            ("pan", "ScaleFactor_Pan"),
        ):
            value = _to_float(attrs.get(attr_name))
            if value is not None:
                scale_factor[key] = value
        if scale_factor:
            meta.set_extended_value("radiometry.scale_factor", scale_factor)
    meta.set_extended_value("radiometry.wavelengths_nm", wavelengths_meta)
    meta.set_extended_value("radiometry.fwhm_nm", fwhm_meta)
    mask = [1 if bool(v) else 0 for v in validity_meta]
    meta.set_extended_value("radiometry.valid_band_mask", mask)
    meta.set_extended_value("radiometry.valid_band_count", int(sum(mask)))

    meta.set_extended_value(
        "atmosphere.atmosphere_model", _decode_text(attrs.get("Atmo_profile_info"))
    )

    meta.set_extended_value("quality.cloudy_pixels_percent", cloud_pct)
    meta.set_extended_value("quality.quality_atmosphere_flag", quality_atm)
    meta.set_extended_value("quality.coverage_percent.cloud", cloud_pct)

    meta.set_extended_value(
        "processing.processor_version",
        processor_version or l1_processor_version,
    )
    meta.set_extended_value("processing.processing_datetime_utc", processing_dt)
    meta.set_extended_value(
        "processing.rtm_engine", _decode_text(attrs.get("Atmo_RTM_info"))
    )
    meta.set_extended_value(
        "processing.lut_version", _decode_text(attrs.get("Atm_Lut_version"))
    )
    if processor_name or processor_version:
        meta.set_extended_value(
            "processing.software",
            {
                "name": processor_name,
                "version": processor_version,
            },
        )
    aux_sun_dist = _decode_text(attrs.get("Aux_SunEarthDistance"))
    aux_sun_irr = _decode_text(attrs.get("Aux_SunIrradiance"))
    if aux_sun_dist is not None or aux_sun_irr is not None:
        meta.set_extended_value(
            "processing.aux_solar_refs",
            {
                "sun_earth_distance": aux_sun_dist,
                "sun_irradiance": aux_sun_irr,
            },
        )

    meta.set_extended_value(
        "uncertainty.reflectance_uncertainty_present", bool(uncertainty_present)
    )

    raw_attr_keys = {
        "Atm_LutGeomInfo_RelativeAzimuth",
        "Atm_LutGeomInfo_SunZenith",
        "Atm_LutGeomInfo_ViewZenith",
        "Atmo_profile_info",
        "Atmo_RTM_info",
        "Atm_Lut_version",
        "Aux_SunEarthDistance",
        "Aux_SunIrradiance",
        "Processor_Name",
        "Processor_Version",
        "Processing_Time",
        "Sun_azimuth_angle",
        "Sun_zenith_angle",
        "Product_StartTime",
        "Product_StopTime",
        "Acquisition_Start_Time",
        "Acquisition_Stop_Time",
        "Product_center_lat",
        "Product_center_long",
        "Cloudy_pixels_percentage",
        "L2d_Quality_flags",
    }
    for key in (start_time_key, end_time_key, sun_azimuth_key, sun_zenith_key):
        if key:
            raw_attr_keys.add(key)

    for key in sorted(raw_attr_keys):
        if key in attrs:
            meta.set_extended_value(f"prisma.{key}", _decode_text(attrs.get(key)))


# -------------------------- region --------------------------
def _compute_edges_from_centers(ul_e, ul_n, ur_e, ur_n, ll_e, ll_n, rows, cols):
    """
    Edges from pixel-center corners.
    Called with rows=E (UL→LL samples) and cols=N (UL→UR samples) AFTER transposing.
    """
    if any(v is None for v in (ul_e, ul_n, ur_e, ur_n, ll_e, ll_n)):
        gs.fatal("PRISMA corners missing (need UL, UR, LL).")
    if rows < 2 or cols < 2:
        gs.fatal("Invalid raster shape (<2).")

    ew_c2c = (ur_e - ul_e) / float(cols - 1)  # columns axis = easting
    ns_c2c = (ul_n - ll_n) / float(rows - 1)  # rows axis = northing

    west = ul_e - 0.5 * ew_c2c
    east = ur_e + 0.5 * ew_c2c
    north = ul_n + 0.5 * ns_c2c
    south = ll_n - 0.5 * ns_c2c

    if east <= west or north <= south:
        eastings = [ul_e, ur_e, ll_e]
        northings = [ul_n, ur_n, ll_n]
        ew_span = max(eastings) - min(eastings)
        ns_span = max(northings) - min(northings)
        ew_half = 0.5 * (ew_span / float(max(cols - 1, 1)))
        ns_half = 0.5 * (ns_span / float(max(rows - 1, 1)))
        west = min(eastings) - ew_half
        east = max(eastings) + ew_half
        south = min(northings) - ns_half
        north = max(northings) + ns_half

    return west, east, south, north


def _force_region_exact_for_transposed(geo, rows_E, cols_N):
    west, east, south, north = _compute_edges_from_centers(
        geo.ul_e,
        geo.ul_n,
        geo.ur_e,
        geo.ur_n,
        geo.ll_e,
        geo.ll_n,
        rows=rows_E,
        cols=cols_N,
    )
    gs.run_command("g.region", w=west, e=east, s=south, n=north, quiet=True)
    gs.run_command("g.region", rows=rows_E, cols=cols_N, quiet=True)
    reg = gs.region()
    if int(reg["rows"]) != rows_E or int(reg["cols"]) != cols_N:
        gs.fatal(
            f"Region is {reg['rows']}x{reg['cols']} but transposed data is {rows_E}x{cols_N}"
        )


def _median_spacing(x, y):
    spacings = []
    for dx, dy in (
        (np.diff(x, axis=1), np.diff(y, axis=1)),
        (np.diff(x, axis=0), np.diff(y, axis=0)),
    ):
        dist = np.sqrt(dx * dx + dy * dy)
        finite = dist[np.isfinite(dist)]
        finite = finite[finite > 0]
        if finite.size:
            spacings.append(float(np.nanmedian(finite)))
    return min(spacings) if spacings else None


def _target_transformer_from_location():
    wkt = gs.read_command("g.proj", flags="wf").strip()
    _require(wkt, "Failed to read GRASS location projection.")
    return Transformer.from_crs(CRS.from_epsg(4326), CRS.from_wkt(wkt), always_xy=True)


def _geocode_cube_nearest(data_cube, lat, lon):
    transformer = _target_transformer_from_location()
    x, y = transformer.transform(lon, lat)
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    pixel_size = _median_spacing(x, y)
    _require(pixel_size is not None, "Could not determine target resolution.")
    ewres = pixel_size
    nsres = pixel_size

    finite = np.isfinite(x) & np.isfinite(y)
    _require(np.any(finite), "No finite geolocation points found.")

    west = float(np.nanmin(x[finite]) - 0.5 * ewres)
    east = float(np.nanmax(x[finite]) + 0.5 * ewres)
    south = float(np.nanmin(y[finite]) - 0.5 * nsres)
    north = float(np.nanmax(y[finite]) + 0.5 * nsres)

    cols = int(np.ceil((east - west) / ewres))
    rows = int(np.ceil((north - south) / nsres))
    _require(rows > 0 and cols > 0, "Invalid target grid dimensions for geocoding.")

    src_rows, src_cols = lat.shape
    src_linear = np.arange(src_rows * src_cols, dtype=np.int64)
    x_flat = x.reshape(-1)
    y_flat = y.reshape(-1)
    valid = np.isfinite(x_flat) & np.isfinite(y_flat)

    col_idx = np.rint((x_flat - (west + 0.5 * ewres)) / ewres).astype(np.int64)
    row_idx = np.rint(((north - 0.5 * nsres) - y_flat) / nsres).astype(np.int64)
    valid &= row_idx >= 0
    valid &= row_idx < rows
    valid &= col_idx >= 0
    valid &= col_idx < cols
    _require(np.any(valid), "No source pixels intersect the target grid.")

    row_idx = row_idx[valid]
    col_idx = col_idx[valid]
    src_linear = src_linear[valid]
    x_flat = x_flat[valid]
    y_flat = y_flat[valid]

    center_x = west + (col_idx + 0.5) * ewres
    center_y = north - (row_idx + 0.5) * nsres
    dist2 = (x_flat - center_x) ** 2 + (y_flat - center_y) ** 2
    target_idx = row_idx * cols + col_idx

    order = np.lexsort((dist2, target_idx))
    target_sorted = target_idx[order]
    keep = np.ones(target_sorted.shape[0], dtype=bool)
    keep[1:] = target_sorted[1:] != target_sorted[:-1]
    target_unique = target_sorted[keep]
    src_unique = src_linear[order][keep]

    out_cube = np.full((rows, cols, data_cube.shape[2]), np.nan, dtype=np.float32)
    flat_source = data_cube.reshape(-1, data_cube.shape[2])
    out_cube.reshape(-1, data_cube.shape[2])[target_unique] = flat_source[src_unique]

    return out_cube, {
        "west": west,
        "east": east,
        "south": south,
        "north": north,
        "rows": rows,
        "cols": cols,
        "ewres": ewres,
        "nsres": nsres,
    }


def _set_region_from_grid(grid):
    gs.run_command(
        "g.region",
        w=grid["west"],
        e=grid["east"],
        s=grid["south"],
        n=grid["north"],
        rows=grid["rows"],
        cols=grid["cols"],
        quiet=True,
    )


# -------------------------- writers --------------------------
def _write_float_raster(name, data_2d_float32):
    arr = garray.array(dtype=np.float32)
    arr[:, :] = data_2d_float32
    arr.write(name, null="nan", overwrite=True)


# -------------------------- public core --------------------------
def import_prisma(
    input_path,
    output_name,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
):
    """
    Writes composite rasters (only) following the EnMAP composite flow:
      - pick nearest bands by wavelength,
      - enhance RGB with -p flag, others without,
      - build composite from three band maps,
      - only final composites remain (temp bands removed).
    Reflectance is float32; per-band temp rasters are created on demand and reused across composites.
    """
    he5 = _resolve_he5(input_path)
    prod = load_prisma_l2d(he5, load_pan=False)
    is_l1 = getattr(prod, "product_type", None) == "L1"

    prod_type = getattr(prod, "product_type", None)
    if prod_type in ("L1", "L2C"):
        gs.warning(
            f"PRISMA {prod_type} is in swath geometry; "
            "data will be geocoded to the target CRS during import."
        )

    _require(prod.hco_geo is not None, "HCO geolocation missing.")
    _require(prod.vnir and prod.vnir.dn is not None, "VNIR cube missing.")
    _require(prod.swir and prod.swir.dn is not None, "SWIR cube missing.")

    data_cube, wavelengths, fwhm, provider_validity = concatenate_hyperspectral(prod)
    _require(data_cube.ndim == 3, f"Unexpected data cube shape: {data_cube.shape}")

    # --- a mask where every band is zero
    bg_mask = None  # (N,E)

    # VNIR contribution (consider only kept bands)
    if prod.vnir and prod.vnir.dn is not None and prod.vnir.bands is not None:
        v_idx = prod.vnir.bands.kept_indices
        v_bg = np.all(prod.vnir.dn[:, :, v_idx] == 0, axis=2)  # (N,E)
        bg_mask = v_bg if bg_mask is None else (bg_mask & v_bg)

    # SWIR contribution (consider only kept bands)
    if prod.swir and prod.swir.dn is not None and prod.swir.bands is not None:
        s_idx = prod.swir.bands.kept_indices
        s_bg = np.all(prod.swir.dn[:, :, s_idx] == 0, axis=2)  # (N,E)
        bg_mask = s_bg if bg_mask is None else (bg_mask & s_bg)

    # Apply: set only outside-footprint pixels to NaN across all bands (real 0.0/radiance stays)
    if bg_mask is not None:
        data_cube[bg_mask, :] = np.nan  # GRASS will store these as NULLs on write

    grid = None
    if is_l1 or getattr(prod, "product_type", None) == "L2C":
        data_cube, grid = _geocode_cube_nearest(
            data_cube,
            prod.hco_geo.lat,
            prod.hco_geo.lon,
        )
    use_transpose = grid is None

    source_wavelengths = np.asarray(wavelengths)
    source_fwhm = np.asarray(fwhm) if fwhm is not None else None

    band_validity = [
        bool(provider_validity[k]) and bool(np.isfinite(data_cube[:, :, k]).any())
        for k in range(data_cube.shape[2])
    ]
    if not any(band_validity):
        gs.fatal("No non-NULL bands found.")

    invalid_idx = [k for k, valid in enumerate(band_validity) if not valid]
    if invalid_idx:
        data_cube[:, :, invalid_idx] = np.nan
    wavelengths = np.asarray(wavelengths)
    if fwhm is not None:
        fwhm = np.asarray(fwhm)

    gs.use_temp_region()
    if grid is not None:
        _set_region_from_grid(grid)
    else:
        first_band = data_cube[:, :, 0].T  # (E,N)
        rows_E, cols_N = first_band.shape
        _force_region_exact_for_transposed(prod.hco_geo, rows_E, cols_N)

    # Build list of composites to make.
    wanted = []
    if composites:
        comp_lookup = {k.upper(): (k, v) for k, v in COMPOSITES.items()}
        for comp in composites:
            compu = comp.strip().upper()
            if compu in comp_lookup:
                orig_name, vals = comp_lookup[compu]
                wanted.append((orig_name, vals))
            else:
                gs.warning(f"Unknown composite '{comp}' ignored.")

    if custom_wavelengths:
        if len(custom_wavelengths) != 3:
            gs.fatal(
                "Custom composites must provide exactly 3 wavelengths (e.g., 850,1650,660)"
            )
        wanted.append(("CUSTOM", [float(x) for x in custom_wavelengths]))

    # create temp rasters only for bands we need, and reuse them via a dict keyed by 1-based band index.
    temp_bands = {}  # {band_idx_1based: raster_name}
    created_names = []  # for final cleanup

    def ensure_band_written(idx1):
        """Write data band idx1 (1-based) as a temp raster (E,N) if not already created."""
        if idx1 in temp_bands:
            return temp_bands[idx1]
        # Extract band; data_cube is (N,E,B) with 0-based k
        k = idx1 - 1
        band_2d = data_cube[:, :, k].T if use_transpose else data_cube[:, :, k]
        band_EN = band_2d.astype(np.float32)
        name = _temp_name(f"{output_name}_b{idx1:03d}")
        _write_float_raster(name, band_EN)
        temp_bands[idx1] = name
        created_names.append(name)
        return name

    # Prime the "rgb_enhanced" mapping:
    valid_band_indices = [i + 1 for i, valid in enumerate(band_validity) if valid]
    valid_wavelengths = np.asarray(
        [wavelengths[i - 1] for i in valid_band_indices], dtype=float
    )
    rgb_target = COMPOSITES["rgb"]
    rgb_indices_1b = [
        valid_band_indices[_find_nearest_band_1based(w, valid_wavelengths)]
        for w in rgb_target
    ]
    # Create these bands now and cache
    for idx1 in rgb_indices_1b:
        ensure_band_written(idx1)
    rgb_enhanced = {idx1: temp_bands[idx1] for idx1 in rgb_indices_1b}

    # -------------------------- build full hyperspectral 3D cube (all bands) --------------------------
    try:
        bands_total = int(data_cube.shape[2])

        # 1) Peg 2D region to an existing temp band (guarantees XY extents & 2D res match slices)
        ref_map_for_region = next(iter(rgb_enhanced.values()))
        Module("g.region", raster=ref_map_for_region, quiet=True)

        # 2) Read the (now pegged) 2D region to mirror its XY resolutions into the 3D region
        reg2d = gs.region()
        nsres2d = float(reg2d["nsres"])
        ewres2d = float(reg2d["ewres"])

        # -------- spectral (Z) axis in nanometers --------
        if wavelengths is not None and len(wavelengths) > 0:
            wl = np.asarray(wavelengths, dtype=float)
            if wl.size > 1:
                # Use exact spacing from endpoints (sum of diffs) to avoid accumulating FP error
                tbres_nm = float((wl[-1] - wl[0]) / (bands_total - 1))
            else:
                tbres_nm = 1.0
            bottom_nm = float(wl[0])
            # set t = b + tbres * bands_total to get depth == bands_total
            top_nm = bottom_nm + tbres_nm * bands_total
        else:
            bottom_nm, top_nm, tbres_nm = 0.0, float(bands_total), 1.0

        gs.run_command(
            "g.region",
            nsres3=nsres2d,
            ewres3=ewres2d,
            b=0,
            t=bands_total,
            tbres=1,
            quiet=True,
        )

        # Create and fill the 3D array: (band, row(E), col(N))
        cube = garray.array3d(dtype=np.float32)
        for k in range(bands_total):
            band_2d = data_cube[:, :, k].T if use_transpose else data_cube[:, :, k]
            cube[k, :, :] = band_2d.astype(np.float32)

        # write 3D raster under the final output name
        cube.write(
            mapname=f"{output_name}", null="nan", overwrite=True
        )  # NaNs -> NULLs
        gs.info(
            f"Created 3D raster with all bands: {output_name} ({bands_total} slices)."
        )

        # -------- hyperspectral metadata (JSON) --------
        try:
            wavelengths_meta = source_wavelengths.tolist()
            fwhm_meta = source_fwhm.tolist() if source_fwhm is not None else None
            validity_meta = [bool(v) for v in band_validity]

            _, acquisition_start_raw = _first_attr(
                prod.attrs,
                (
                    "Product_StartTime",
                    "Acquisition_Start_Time",
                ),
            )
            acquisition_datetime = _to_iso_utc(acquisition_start_raw)

            meta = HyperMetadata.for_spectral_data(
                wavelengths=wavelengths_meta,
                fwhm=fwhm_meta,
                sensor="PRISMA",
                radiometric_quantity=(
                    "toa_radiance" if is_l1 else "surface_reflectance"
                ),
                radiometric_units=("W/(m^2 sr um)" if is_l1 else "unitless"),
                acquisition_datetime=acquisition_datetime,
            )
            meta.set_validity(validity_meta)

            _populate_prisma_extended_metadata(
                meta=meta,
                he5_path=he5,
                prod=prod,
                wavelengths_meta=wavelengths_meta,
                fwhm_meta=fwhm_meta,
                validity_meta=validity_meta,
            )

            mapset = gs.gisenv().get("MAPSET", "")
            out_full = (
                f"{output_name}@{mapset}"
                if mapset and "@" not in output_name
                else output_name
            )
            cmd = [
                "i.hyper.import",
                f"input={shlex.quote(he5)}",
                "product=prisma",
                f"output={output_name}",
                f"strength={strength_val}",
            ]
            if composites:
                cmd.append(f"composites={','.join(composites)}")
            if custom_wavelengths:
                cmd.append(
                    "composites_custom=" + ",".join(str(v) for v in custom_wavelengths)
                )
            meta.add_history_entry(
                command=" ".join(cmd),
                inputs=[],
                outputs=[{"id": meta.dataset_id, "map_name": out_full}],
            )
            meta.save(output_name, save_region=True)
        except Exception as e_meta:
            gs.warning(f"Failed to write r3 metadata: {e_meta}")
        # -----------------------------------------------------------------
    except Exception as e:
        gs.warning(f"3D cube creation failed: {e}")
    # -------------------------------------------------------------------------------------------------------

    # For each requested composite, select bands and build r.composite
    for name, targets in wanted:
        bands_1b = [
            valid_band_indices[_find_nearest_band_1based(w, valid_wavelengths)]
            for w in targets
        ]
        rgb_maps = []
        for idx1 in bands_1b:
            if idx1 in rgb_enhanced:
                rgb_maps.append(rgb_enhanced[idx1])
            else:
                rgb_maps.append(ensure_band_written(idx1))

        Module("g.region", raster=rgb_maps[0], quiet=True)
        if name.upper() == "RGB":
            Module(
                "i.colors.enhance",
                red=rgb_maps[0],
                green=rgb_maps[1],
                blue=rgb_maps[2],
                strength=str(strength_val),
                flags="p",
                quiet=True,
            )
            outname = f"{output_name}_{name.lower().replace('-', '_')}"
        else:
            Module(
                "i.colors.enhance",
                red=rgb_maps[0],
                green=rgb_maps[1],
                blue=rgb_maps[2],
                strength=str(strength_val),
                quiet=True,
            )
            outname = f"{output_name}_{name.lower().replace('-', '_')}"

        Module(
            "r.composite",
            red=rgb_maps[0],
            green=rgb_maps[1],
            blue=rgb_maps[2],
            output=outname,
            quiet=True,
            overwrite=True,
        )
        gs.info(f"Generated composite raster: {outname}")

    # Clean up temp bands after all composites are made
    if created_names:
        Module(
            "g.remove",
            type="raster",
            name=",".join(created_names),
            flags="f",
            quiet=True,
        )

    gs.del_temp_region()


def run_import(options, flags):
    custom = None
    if options.get("composites_custom"):
        try:
            custom = [float(x.strip()) for x in options["composites_custom"].split(",")]
            if len(custom) != 3:
                raise ValueError
        except Exception:
            gs.fatal(
                "Invalid format for composites_custom. Usage example: 850,1650,660"
            )

    strength_opt = options.get("strength")
    if strength_opt is None or str(strength_opt).strip() == "":
        strength_val = 96
    else:
        try:
            strength_val = int(str(strength_opt).strip())
        except Exception:
            gs.fatal("Invalid strength. Provide an integer 0-100.")
        if not (0 <= strength_val <= 100):
            gs.fatal("Invalid strength. Provide an integer 0-100.")

    comps = (
        [c.strip() for c in options["composites"].split(",")]
        if options.get("composites")
        else None
    )
    import_prisma(
        input_path=options["input"],
        output_name=options["output"],
        composites=comps,
        custom_wavelengths=custom,
        strength_val=strength_val,
    )
