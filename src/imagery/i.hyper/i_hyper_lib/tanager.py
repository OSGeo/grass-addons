#!/usr/bin/env python3
"""
Tanager → GRASS

- Imports Tanager BASIC and orthorectified products (radiance or surface_reflectance)
- BASIC: projects and resamples to target map grid defined by Planet_Ortho_Framing
  using bilinear forward splatting with small-neighborhood nearest fill for purely
  geometric gaps (optional; SciPy if available)
- ORTHO: imports directly in native map grid
- Writes a full 3D raster (bands in Z) and per-band composites
- Preserves nodata (nodata_pixels==1) as NULLs in GRASS
"""

import os
import uuid
import shlex
from datetime import datetime, timezone
import numpy as np
import h5py
import grass.script as gs
import grass.script.array as garray
from grass.pygrass.modules import Module

from hyper_meta import HyperMetadata
from tanager_reader import (
    load_tanager_basic,
    read_planet_map_grid,
    map_grid_center_lonlat,
    build_splat_plan,
    project_band_to_map_grid,
)

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


def _resolve_h5(path_like):
    if os.path.isdir(path_like):
        try:
            names = sorted(os.listdir(path_like))
        except Exception as e:
            gs.fatal(f"Cannot read folder '{path_like}': {e}")
        for n in names:
            if n.lower().endswith(".h5"):
                return os.path.join(path_like, n)
        gs.fatal("No .h5 file found in the provided folder.")
    return path_like


def _find_nearest_band_1based(target_nm, wavelengths_nm):
    wl = np.asarray(wavelengths_nm, dtype=np.float32)
    return int(np.argmin(np.abs(wl - float(target_nm)))) + 1  # 1-based


def _temp_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _write_float_raster(name, data_2d_float32):
    arr = garray.array(dtype=np.float32)
    arr[:, :] = data_2d_float32
    arr.write(name, null="nan", overwrite=True)  # NaNs -> NULLs


def _decode_text(value):
    if value is None:
        return None
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


def _relative_azimuth(sun_azimuth, view_azimuth):
    if sun_azimuth is None or view_azimuth is None:
        return None
    return abs((float(view_azimuth) - float(sun_azimuth) + 180.0) % 360.0 - 180.0)


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _to_iso_from_epoch(value):
    if value is None:
        return None
    try:
        fv = float(value)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(fv) or fv <= 0:
        return None
    # Planet/Tanager time fields are Unix seconds in available samples.
    if fv < 1e8 or fv > 1e11:
        return None
    return (
        datetime.fromtimestamp(fv, tz=timezone.utc).isoformat().replace("+00:00", "Z")
    )


def _line_time_summary(values):
    vals = np.asarray(values).ravel()
    vals = vals[np.isfinite(vals)]
    vals = vals[vals > 0]
    if vals.size == 0:
        return None
    vals = np.sort(vals.astype(np.float64, copy=False))
    diffs = np.diff(vals) if vals.size > 1 else np.array([], dtype=np.float64)
    diffs = diffs[np.isfinite(diffs)]
    return {
        "count": int(vals.size),
        "min": _to_iso_from_epoch(vals[0]) or float(vals[0]),
        "max": _to_iso_from_epoch(vals[-1]) or float(vals[-1]),
        "step_seconds": float(np.nanmean(diffs)) if diffs.size else None,
    }


def _mean_dataset(h5obj, path, nodata_mask=None):
    if path not in h5obj:
        return None
    ds = h5obj[path]
    arr = np.asarray(ds[()], dtype=np.float64)
    valid = np.isfinite(arr)
    fill = ds.attrs.get("_FillValue") if hasattr(ds, "attrs") else None
    if fill is not None:
        valid &= arr != float(fill)
    if nodata_mask is not None and nodata_mask.shape == arr.shape:
        valid &= ~nodata_mask
    vals = arr[valid]
    if vals.size == 0:
        return None
    return float(np.nanmean(vals))


def _coverage_percent(mask_arr, nodata_mask=None):
    if mask_arr is None:
        return None
    arr = np.asarray(mask_arr)
    if arr.size == 0:
        return None
    valid = np.isfinite(arr)
    if nodata_mask is not None and nodata_mask.shape == arr.shape:
        valid &= ~nodata_mask
    vals = arr[valid]
    if vals.size == 0:
        return None
    return float(np.mean(vals.astype(np.float64) > 0) * 100.0)


def _populate_tanager_extended_metadata(
    meta,
    h5_path,
    prod,
    wavelengths_meta,
    fwhm_meta,
    validity_meta,
    grid=None,
):
    with h5py.File(h5_path, "r") as f:
        if "/HDFEOS/SWATHS/HYP" in f:
            root = "/HDFEOS/SWATHS/HYP"
            product_layout = "swaths"
        elif "/HDFEOS/GRIDS/HYP" in f:
            root = "/HDFEOS/GRIDS/HYP"
            product_layout = "grids"
        else:
            return

        data_group = f"{root}/Data Fields"
        geo_group = f"{root}/Geolocation Fields"

        created_at = _to_iso_utc(f[root].attrs.get("created_at"))
        strip_id = _decode_text(f[root].attrs.get("strip_id"))
        epsg_code = _to_int(f[root].attrs.get("epsg_code"))

        nodata_mask = None
        nodata_path = f"{data_group}/nodata_pixels"
        if nodata_path in f:
            nodata_mask = np.asarray(f[nodata_path][()]) > 0

        time_path = None
        if f"{data_group}/time" in f:
            time_path = f"{data_group}/time"
        elif f"{geo_group}/Time" in f:
            time_path = f"{geo_group}/Time"

        start_time = None
        end_time = None
        line_time = None
        if time_path is not None:
            tds = f[time_path]
            tarr = np.asarray(tds[()], dtype=np.float64)
            valid = np.isfinite(tarr)
            fill = tds.attrs.get("_FillValue") if hasattr(tds, "attrs") else None
            if fill is not None:
                valid &= tarr != float(fill)
            if nodata_mask is not None and nodata_mask.shape == tarr.shape:
                valid &= ~nodata_mask
            valid &= tarr > 0
            tvals = tarr[valid]
            if tvals.size > 0:
                tmin = float(np.min(tvals))
                tmax = float(np.max(tvals))
                start_time = _to_iso_from_epoch(tmin)
                end_time = _to_iso_from_epoch(tmax)
                line_time = _line_time_summary(tvals)

        if start_time:
            meta.acquisition_datetime = start_time

        center_lat = None
        center_lon = None
        if (
            getattr(prod, "lat", None) is not None
            and getattr(prod, "lon", None) is not None
        ):
            lat = np.asarray(prod.lat, dtype=np.float64)
            lon = np.asarray(prod.lon, dtype=np.float64)
            vlat = np.isfinite(lat)
            vlon = np.isfinite(lon)
            if nodata_mask is not None and nodata_mask.shape == lat.shape:
                vlat &= ~nodata_mask
                vlon &= ~nodata_mask
            if np.any(vlat):
                center_lat = float(np.nanmean(lat[vlat]))
            if np.any(vlon):
                center_lon = float(np.nanmean(lon[vlon]))

        if (center_lat is None or center_lon is None) and grid is not None:
            latc, lonc = map_grid_center_lonlat(grid)
            if center_lat is None:
                center_lat = latc
            if center_lon is None:
                center_lon = lonc

        sun_zenith = _mean_dataset(
            f, f"{data_group}/sun_zenith", nodata_mask=nodata_mask
        )
        sun_azimuth = _mean_dataset(
            f, f"{data_group}/sun_azimuth", nodata_mask=nodata_mask
        )
        view_zenith = _mean_dataset(
            f, f"{data_group}/sensor_zenith", nodata_mask=nodata_mask
        )
        view_azimuth = _mean_dataset(
            f, f"{data_group}/sensor_azimuth", nodata_mask=nodata_mask
        )
        rel_azimuth = _relative_azimuth(sun_azimuth, view_azimuth)

        aod_mean = _mean_dataset(
            f, f"{data_group}/aerosol_optical_depth", nodata_mask=nodata_mask
        )
        h2o_mean = _mean_dataset(
            f, f"{data_group}/column_water_vapour", nodata_mask=nodata_mask
        )
        path_length_mean = _mean_dataset(
            f, f"{data_group}/sensor_to_ground_path_length", nodata_mask=nodata_mask
        )

        cloud_mask = (
            np.asarray(f[f"{data_group}/beta_cloud_mask"][()])
            if f"{data_group}/beta_cloud_mask" in f
            else None
        )
        cirrus_mask = (
            np.asarray(f[f"{data_group}/beta_cirrus_mask"][()])
            if f"{data_group}/beta_cirrus_mask" in f
            else None
        )

        cloud_pct = _coverage_percent(cloud_mask, nodata_mask=nodata_mask)
        cirrus_pct = _coverage_percent(cirrus_mask, nodata_mask=nodata_mask)

        uncertainty_present = f"{data_group}/surface_reflectance_uncertainty" in f

        applied_coeffs = None
        if f"{data_group}/toa_radiance" in f:
            ds_rad = f[f"{data_group}/toa_radiance"]
            if "applied_radiometric_coefficients" in ds_rad.attrs:
                applied_coeffs = np.asarray(
                    ds_rad.attrs["applied_radiometric_coefficients"]
                ).tolist()

        meta.set_extended_value("acquisition.start_time_utc", start_time)
        meta.set_extended_value("acquisition.end_time_utc", end_time)
        meta.set_extended_value("acquisition.center_latitude_deg", center_lat)
        meta.set_extended_value("acquisition.center_longitude_deg", center_lon)
        meta.set_extended_value("acquisition.day_of_year", _day_of_year(start_time))
        meta.set_extended_value("acquisition.line_time_summary", line_time)

        meta.set_extended_value("geometry.sun_zenith_deg", sun_zenith)
        meta.set_extended_value("geometry.sun_azimuth_deg", sun_azimuth)
        meta.set_extended_value("geometry.view_zenith_deg", view_zenith)
        meta.set_extended_value("geometry.view_azimuth_deg", view_azimuth)
        meta.set_extended_value("geometry.relative_azimuth_deg", rel_azimuth)
        if path_length_mean is not None:
            meta.set_extended_form_value(
                "geometry.sensor_to_ground_path_length_m",
                value=path_length_mean,
                form="map_mean",
                source="sensor_to_ground_path_length",
            )

        meta.set_extended_value(
            "radiometry.quantity", getattr(prod, "data_field", None)
        )
        meta.set_extended_value("radiometry.units", getattr(prod, "data_units", None))
        meta.set_extended_value("radiometry.wavelengths_nm", wavelengths_meta)
        meta.set_extended_value("radiometry.fwhm_nm", fwhm_meta)
        mask = [1 if bool(v) else 0 for v in validity_meta]
        meta.set_extended_value("radiometry.valid_band_mask", mask)
        meta.set_extended_value("radiometry.valid_band_count", int(sum(mask)))
        meta.set_extended_value(
            "radiometry.applied_radiometric_coefficients", applied_coeffs
        )

        if aod_mean is not None:
            meta.set_extended_form_value(
                "atmosphere.aod_550",
                value=aod_mean,
                form="map_mean",
                source="aerosol_optical_depth",
            )
        if h2o_mean is not None:
            meta.set_extended_form_value(
                "atmosphere.h2o_g_cm2",
                value=h2o_mean,
                form="map_mean",
                source="column_water_vapour",
            )

        meta.set_extended_value("quality.coverage_percent.cloud", cloud_pct)
        meta.set_extended_value("quality.coverage_percent.cirrus", cirrus_pct)
        meta.set_extended_value(
            "quality.mask_layers",
            {
                "beta_cloud_mask": f"{data_group}/beta_cloud_mask" in f,
                "beta_cirrus_mask": f"{data_group}/beta_cirrus_mask" in f,
                "nodata_pixels": nodata_path in f,
            },
        )

        meta.set_extended_value("processing.processing_datetime_utc", created_at)
        meta.set_extended_value(
            "uncertainty.reflectance_uncertainty_present", bool(uncertainty_present)
        )
        meta.set_extended_value("tanager.product_layout", product_layout)

        meta.set_extended_value(
            "tanager.map_refs.sun_zenith",
            f"{data_group}/sun_zenith" if f"{data_group}/sun_zenith" in f else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.sun_azimuth",
            f"{data_group}/sun_azimuth" if f"{data_group}/sun_azimuth" in f else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.sensor_zenith",
            f"{data_group}/sensor_zenith"
            if f"{data_group}/sensor_zenith" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.sensor_azimuth",
            f"{data_group}/sensor_azimuth"
            if f"{data_group}/sensor_azimuth" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.sensor_to_ground_path_length",
            f"{data_group}/sensor_to_ground_path_length"
            if f"{data_group}/sensor_to_ground_path_length" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.aerosol_optical_depth",
            f"{data_group}/aerosol_optical_depth"
            if f"{data_group}/aerosol_optical_depth" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.column_water_vapour",
            f"{data_group}/column_water_vapour"
            if f"{data_group}/column_water_vapour" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.map_refs.surface_reflectance_uncertainty",
            f"{data_group}/surface_reflectance_uncertainty"
            if f"{data_group}/surface_reflectance_uncertainty" in f
            else None,
        )
        meta.set_extended_value(
            "tanager.quality_masks.beta_cloud_mask",
            f"{data_group}/beta_cloud_mask" in f,
        )
        meta.set_extended_value(
            "tanager.quality_masks.beta_cirrus_mask",
            f"{data_group}/beta_cirrus_mask" in f,
        )
        meta.set_extended_value("tanager.quality_masks.nodata_pixels", nodata_path in f)
        meta.set_extended_value("tanager.created_at", created_at)
        meta.set_extended_value("tanager.strip_id", strip_id)
        meta.set_extended_value("tanager.epsg_code", epsg_code)


# -------------------------- core --------------------------


def import_tanager(
    input_path,
    output_name,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
    import_null=False,
    fill_8_neighbor=True,
):
    """
    Import Tanager BASIC and orthorectified products to the target map grid. Writes:
      - 3D raster (bands as slices)
      - per-band temporary rasters for composites
      - color-enhanced composites

    Parameters:
      fill_8_neighbor: if True and SciPy is available, fills only geometric gaps
                       via nearest neighbor limited to the 8-neighborhood.
    """
    h5 = _resolve_h5(input_path)
    prod = load_tanager_basic(h5)

    if getattr(prod, "product_layout", None) == "swaths":
        gs.warning(
            "Tanager BASIC is in swath geometry; "
            "data will be projected to the target map grid during import."
        )

    data = prod.data  # (rows, cols, bands), float32 with NaNs where nodata_pixels==1
    wl = prod.wavelengths_nm
    fwhm = prod.fwhm_nm

    _require(data is not None and data.ndim == 3, "Data cube missing or invalid.")

    use_splat = getattr(prod, "product_layout", "swaths") == "swaths"
    if use_splat:
        _require(
            prod.lat is not None and prod.lon is not None,
            "Latitude/Longitude grids missing.",
        )

    source_wavelengths = np.asarray(wl)
    source_fwhm = np.asarray(fwhm) if fwhm is not None else None

    # Per-band validity before reprojection (nodata already set to NaN in loader)
    band_validity = [
        bool(np.isfinite(data[:, :, k]).any()) for k in range(data.shape[2])
    ]
    keep = [k for k, valid in enumerate(band_validity) if valid]
    if not keep:
        gs.fatal("No non-NULL bands found.")
    data = data[:, :, keep]
    wl = np.asarray(wl)[keep]
    if fwhm is not None:
        fwhm = np.asarray(fwhm)[keep]

    # composites list
    wanted = []
    if composites:
        lut = {k.upper(): (k, v) for k, v in COMPOSITES.items()}
        for comp in composites:
            key = comp.strip().upper()
            if key in lut:
                name, vals = lut[key]
                wanted.append((name, vals))
            else:
                gs.warning(f"Ignored unknown composite '{comp}'.")
    else:
        wanted.append(("rgb", COMPOSITES["rgb"]))

    if custom_wavelengths:
        if len(custom_wavelengths) != 3:
            gs.fatal(
                "Custom composites must provide exactly 3 wavelengths, e.g. 850,1650,660"
            )
        wanted.append(("CUSTOM", [float(x) for x in custom_wavelengths]))

    gs.use_temp_region()

    # Read Planet target map grid and set region
    grid = read_planet_map_grid(h5)
    # Always lock region dimensions to product grid rows/cols. Using resolution
    # alignment (-a) can expand the region by 1-2 cells on some platforms and
    # break array writes when projected bands keep original metadata dimensions.
    Module(
        "g.region",
        w=grid.west,
        e=grid.east,
        s=grid.south,
        n=grid.north,
        rows=grid.rows,
        cols=grid.cols,
        quiet=True,
    )

    # Precompute the per-scene splat plan for BASIC products.
    plan = None
    if use_splat:
        # Use a band-independent nodata mask (after loader has applied nodata across all bands).
        base_mask = np.isnan(data[..., 0])
        plan = build_splat_plan(prod.lon, prod.lat, grid, nodata_mask=base_mask)
    else:
        _require(
            data.shape[0] == grid.rows and data.shape[1] == grid.cols,
            "Orthorectified Tanager dimensions do not match product map grid.",
        )

    # Band writer using projection + gridding and caching
    temp_bands = {}
    created_names = []

    def ensure_band_written(idx1):
        if idx1 in temp_bands:
            return temp_bands[idx1]
        k = idx1 - 1
        if use_splat:
            ortho2d = project_band_to_map_grid(
                band2d=data[:, :, k], plan=plan, fill_8_neighbor=fill_8_neighbor
            )
        else:
            ortho2d = np.asarray(data[:, :, k], dtype=np.float32)
        name = _temp_name(f"{output_name}_b{idx1:03d}")
        _write_float_raster(name, ortho2d)
        temp_bands[idx1] = name
        created_names.append(name)
        return name

    # -------------------------- 3D cube write --------------------------
    bands_total = int(data.shape[2])
    try:
        # Mirror 2D res into 3D; Z is band index
        reg2d = gs.region()
        nsres2d = float(reg2d["nsres"])
        ewres2d = float(reg2d["ewres"])
        Module(
            "g.region",
            nsres3=nsres2d,
            ewres3=ewres2d,
            b=0,
            t=bands_total,
            tbres=1,
            quiet=True,
        )

        cube = garray.array3d(dtype=np.float32)
        for k in range(bands_total):
            if use_splat:
                ortho2d = project_band_to_map_grid(
                    band2d=data[:, :, k], plan=plan, fill_8_neighbor=fill_8_neighbor
                )
            else:
                ortho2d = np.asarray(data[:, :, k], dtype=np.float32)
            cube[k, :, :] = ortho2d

        cube.write(mapname=f"{output_name}", null="nan", overwrite=True)
        gs.info(
            f"Created 3D raster with all bands: {output_name} ({bands_total} slices)."
        )

        # hyperspectral metadata (JSON)
        try:
            if import_null:
                wavelengths_meta = source_wavelengths.tolist()
                fwhm_meta = source_fwhm.tolist() if source_fwhm is not None else None
                validity_meta = [bool(v) for v in band_validity]
            else:
                wavelengths_meta = wl.tolist()
                fwhm_meta = fwhm.tolist() if fwhm is not None else None
                validity_meta = [True] * len(wavelengths_meta)

            meta = HyperMetadata.for_spectral_data(
                wavelengths=wavelengths_meta,
                fwhm=fwhm_meta,
                sensor="Tanager",
                radiometric_quantity=getattr(prod, "data_field", None),
                radiometric_units=getattr(prod, "data_units", None),
            )
            meta.set_validity(validity_meta)

            _populate_tanager_extended_metadata(
                meta=meta,
                h5_path=h5,
                prod=prod,
                wavelengths_meta=wavelengths_meta,
                fwhm_meta=fwhm_meta,
                validity_meta=validity_meta,
                grid=grid,
            )

            mapset = gs.gisenv().get("MAPSET", "")
            out_full = (
                f"{output_name}@{mapset}"
                if mapset and "@" not in output_name
                else output_name
            )
            cmd = [
                "i.hyper.import",
                f"input={shlex.quote(h5)}",
                "product=tanager",
                f"output={output_name}",
                f"strength={strength_val}",
            ]
            if composites:
                cmd.append(f"composites={','.join(composites)}")
            if custom_wavelengths:
                cmd.append(
                    "composites_custom=" + ",".join(str(v) for v in custom_wavelengths)
                )
            if import_null:
                cmd.append("-n")

            meta.add_history_entry(
                command=" ".join(cmd),
                inputs=[],
                outputs=[{"id": meta.dataset_id, "map_name": out_full}],
            )
            meta.save(output_name, save_region=True)
        except Exception as e_meta:
            gs.warning(f"Failed to write r3 metadata: {e_meta}")
    except Exception as e:
        gs.warning(f"3D cube creation failed: {e}")

    # -------------------------- composites --------------------------
    rgb_target = COMPOSITES["rgb"]
    rgb_indices_1b = [_find_nearest_band_1based(w, wl) for w in rgb_target]
    for idx1 in rgb_indices_1b:
        ensure_band_written(idx1)
    ref_map = next(iter({i: temp_bands[i] for i in rgb_indices_1b}.values()))
    Module("g.region", raster=ref_map, quiet=True)

    for name, targets in wanted:
        bands_1b = [_find_nearest_band_1based(w, wl) for w in targets]
        maps = []
        for idx1 in bands_1b:
            maps.append(
                temp_bands[idx1] if idx1 in temp_bands else ensure_band_written(idx1)
            )

        Module("g.region", raster=maps[0], quiet=True)
        if name.upper() == "RGB":
            Module(
                "i.colors.enhance",
                red=maps[0],
                green=maps[1],
                blue=maps[2],
                strength=str(strength_val),
                flags="p",
                quiet=True,
            )
        else:
            Module(
                "i.colors.enhance",
                red=maps[0],
                green=maps[1],
                blue=maps[2],
                strength=str(strength_val),
                quiet=True,
            )

        outname = f"{output_name}_{name.lower().replace('-', '_')}"
        Module(
            "r.composite",
            red=maps[0],
            green=maps[1],
            blue=maps[2],
            output=outname,
            quiet=True,
            overwrite=True,
        )
        gs.info(f"Generated composite raster: {outname}")

    # cleanup
    if created_names:
        Module(
            "g.remove",
            type="raster",
            name=",".join(created_names),
            flags="f",
            quiet=True,
        )

    gs.del_temp_region()


# -------------------------- entry --------------------------


def run_import(options, flags):
    custom = None
    if options.get("composites_custom"):
        try:
            custom = [float(x.strip()) for x in options["composites_custom"].split(",")]
            if len(custom) != 3:
                raise ValueError
        except Exception:
            gs.fatal("Invalid format for composites_custom. Example: 850,1650,660")

    strength_opt = options.get("strength")
    if strength_opt is None or str(strength_opt).strip() == "":
        strength_val = 96
    else:
        try:
            strength_val = int(str(strength_opt).strip())
        except Exception:
            gs.fatal("Invalid strength. Provide an integer 0–100.")
        if not (0 <= strength_val <= 100):
            gs.fatal("Invalid strength. Provide an integer 0–100.")

    comps = (
        [c.strip() for c in options["composites"].split(",")]
        if options.get("composites")
        else None
    )
    import_null = bool(flags.get("n"))

    import_tanager(
        input_path=options["input"],
        output_name=options["output"],
        composites=comps,
        custom_wavelengths=custom,
        strength_val=strength_val,
        import_null=import_null,
        fill_8_neighbor=True,
    )
