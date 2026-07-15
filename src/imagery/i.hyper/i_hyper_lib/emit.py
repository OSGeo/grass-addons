#!/usr/bin/env python3
"""
EMIT → GRASS

- Imports EMIT L2A Reflectance NetCDF products
- Orthorectifies via GLT lookup tables
- Writes a full 3D raster (bands in Z) and per-band composites
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

COMPOSITES = {
    "rgb": [660, 572, 478],
    "cir": [848, 660, 572],
    "swir_agriculture": [848, 1653, 660],
    "swir_geology": [2200, 848, 572],
}

# -------------------------- helpers --------------------------


def _require(cond, msg):
    if not cond:
        gs.fatal(msg)


def _resolve_nc(path_like):
    if os.path.isdir(path_like):
        try:
            names = sorted(os.listdir(path_like))
        except Exception as e:
            gs.fatal(f"Cannot read folder '{path_like}': {e}")
        for n in names:
            if n.lower().endswith(".nc"):
                return os.path.join(path_like, n)
        gs.fatal("No .nc file found in the provided folder.")
    return path_like


def _find_nearest_band_1based(target_nm, wavelengths_nm):
    wl = np.asarray(wavelengths_nm, dtype=np.float32)
    return int(np.argmin(np.abs(wl - float(target_nm)))) + 1


def _temp_name(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _write_float_raster(name, data_2d_float32):
    arr = garray.array(dtype=np.float32)
    arr[:, :] = data_2d_float32
    arr.write(name, null="nan", overwrite=True)


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


def _to_float(value):
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


def _to_int(value):
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


# -------------------------- EMIT NetCDF reader (inline) --------------------------


def _read_emit_netcdf(path):
    with h5py.File(path, "r") as f:
        glt_x = np.asarray(f["location/glt_x"][()], dtype=np.int32)
        glt_y = np.asarray(f["location/glt_y"][()], dtype=np.int32)

        ortho_rows, ortho_cols = glt_y.shape

        gt = f.attrs["geotransform"]
        west = float(gt[0])
        ewres = float(gt[1])
        north = float(gt[3])
        nsres = abs(float(gt[5]))
        east = west + ortho_cols * ewres
        south = north - ortho_rows * nsres

        data_key = "reflectance" if "reflectance" in f else "radiance"
        raw = np.asarray(f[data_key][()], dtype=np.float32)
        _require(raw.ndim == 3, f"{data_key} is not 3D")

        raw_fill = f[data_key].attrs.get("_FillValue", -9999.0)
        if isinstance(raw_fill, np.ndarray):
            raw_fill = raw_fill.item() if raw_fill.size > 0 else -9999.0
        raw[np.isclose(raw, float(raw_fill))] = np.nan

        wl = np.asarray(f["sensor_band_parameters/wavelengths"][()], dtype=np.float32)
        fwhm = np.asarray(
            f["sensor_band_parameters/fwhm"][()], dtype=np.float32
        )
        if "good_wavelengths" in f["sensor_band_parameters"]:
            good = np.asarray(
                f["sensor_band_parameters/good_wavelengths"][()], dtype=np.uint8
            )
        else:
            good = np.ones(wl.shape, dtype=np.uint8)

        order = np.argsort(wl)
        wl = wl[order]
        fwhm = fwhm[order]
        good = good[order]
        raw = raw[:, :, order]

        lat_ds = f["location/lat"][()] if "location/lat" in f else None
        lon_ds = f["location/lon"][()] if "location/lon" in f else None
        lat = np.asarray(lat_ds, dtype=np.float64) if lat_ds is not None else None
        lon = np.asarray(lon_ds, dtype=np.float64) if lon_ds is not None else None
        attrs = {}
        for k in f.attrs.keys():
            try:
                attrs[k] = _decode_text(f.attrs[k])
            except Exception:
                attrs[k] = str(f.attrs[k])

    return {
        "data": raw,
        "wavelengths": wl,
        "fwhm": fwhm,
        "good_wavelengths": good,
        "data_key": data_key,
        "glt_x": glt_x,
        "glt_y": glt_y,
        "ortho_rows": ortho_rows,
        "ortho_cols": ortho_cols,
        "west": west,
        "east": east,
        "south": south,
        "north": north,
        "ewres": ewres,
        "nsres": nsres,
        "lat": lat,
        "lon": lon,
        "attrs": attrs,
    }


# -------------------------- GLT orthorectification --------------------------


def _orthorectify_band(band2d, glt_y, glt_x):
    valid = (glt_y > 0) & (glt_x > 0)
    if not np.any(valid):
        return np.full(glt_y.shape, np.nan, dtype=np.float32)
    ortho = np.full(glt_y.shape, np.nan, dtype=np.float32)
    r = glt_y[valid] - 1
    c = glt_x[valid] - 1
    ortho[valid] = band2d[r, c]
    return ortho


# -------------------------- extended metadata --------------------------


def _populate_emit_extended_metadata(
    meta, prod, wavelengths_meta, fwhm_meta, validity_meta
):
    attrs = prod["attrs"]

    start_time = _to_iso_utc(attrs.get("time_coverage_start"))
    end_time = _to_iso_utc(attrs.get("time_coverage_end"))
    created_at = _to_iso_utc(attrs.get("date_created"))

    center_lat = None
    center_lon = None
    if prod["lat"] is not None and prod["lon"] is not None:
        valid = (
            np.isfinite(prod["lat"])
            & np.isfinite(prod["lon"])
            & (prod["lat"] > -9990)
            & (prod["lon"] > -9990)
        )
        if np.any(valid):
            center_lat = float(np.nanmean(prod["lat"][valid]))
            center_lon = float(np.nanmean(prod["lon"][valid]))

    meta.set_extended_value("acquisition.start_time_utc", start_time)
    meta.set_extended_value("acquisition.end_time_utc", end_time)
    meta.set_extended_value("acquisition.center_latitude_deg", center_lat)
    meta.set_extended_value("acquisition.center_longitude_deg", center_lon)
    meta.set_extended_value("acquisition.day_of_year", _day_of_year(start_time))

    is_radiance = prod.get("data_key") == "radiance"
    meta.set_extended_value(
        "radiometry.quantity",
        "at-sensor_radiance" if is_radiance else "surface_reflectance",
    )
    meta.set_extended_value(
        "radiometry.units",
        "W/m^2/sr/nm" if is_radiance else "unitless (reflectance)",
    )
    meta.set_extended_value("radiometry.wavelengths_nm", wavelengths_meta)
    meta.set_extended_value("radiometry.fwhm_nm", fwhm_meta)
    mask = [1 if bool(v) else 0 for v in validity_meta]
    meta.set_extended_value("radiometry.valid_band_mask", mask)
    meta.set_extended_value("radiometry.valid_band_count", int(sum(mask)))

    meta.set_extended_value("processing.processing_datetime_utc", created_at)
    meta.set_extended_value(
        "processing.software_build_version",
        attrs.get("software_build_version"),
    )
    meta.set_extended_value(
        "processing.product_version", attrs.get("product_version")
    )

    meta.set_extended_value("emit.flight_line", attrs.get("flight_line"))
    meta.set_extended_value("emit.day_night_flag", attrs.get("day_night_flag"))

    n_valid_glt = int(np.count_nonzero((prod["glt_y"] > 0) & (prod["glt_x"] > 0)))
    total_ortho = prod["ortho_rows"] * prod["ortho_cols"]
    coverage = float(n_valid_glt) / total_ortho * 100.0 if total_ortho else None
    meta.set_extended_value("quality.coverage_percent.ortho_grid", coverage)

    meta.set_extended_value(
        "emit.geotransform",
        [prod["west"], prod["ewres"], 0, prod["north"], 0, -prod["nsres"]],
    )
    meta.set_extended_value("emit.spatial_resolution_deg", prod["ewres"])


# -------------------------- projection info for -p flag --------------------------


def get_emit_proj_info(path):
    """Return CRS/spatial info dict for an EMIT product.

    EMIT L2A/L1B → orthorectified grid (EPSG:4326).
    """
    nc = _resolve_nc(path)
    with h5py.File(nc, "r") as f:
        glt_y = f["location/glt_y"]
        ortho_rows, ortho_cols = glt_y.shape

        gt = f.attrs["geotransform"]
        west = float(gt[0])
        ewres = float(gt[1])
        north = float(gt[3])
        nsres = abs(float(gt[5]))
        east = west + ortho_cols * ewres
        south = north - ortho_rows * nsres

        product_type = "L2A" if "reflectance" in f else "L1B"

    return {
        "product_type": product_type,
        "layout": "grid",
        "srid": "EPSG:4326",
        "west": west,
        "east": east,
        "south": south,
        "north": north,
        "rows": ortho_rows,
        "cols": ortho_cols,
        "ewres": ewres,
        "nsres": nsres,
        "import_behavior": (
            "Uses the product GLT lookup tables to orthorectify the raw data "
            "onto a WGS84 grid."
        ),
        "project_requirements": (
            "Use a GRASS project whose CRS matches the product CRS for best "
            "results, but also supports any projected CRS via forward "
            "bilinear splatting."
        ),
    }


# -------------------------- core import --------------------------


def import_emit(
    input_path,
    output_name,
    composites=None,
    custom_wavelengths=None,
    strength_val=96,
    import_null=False,
):
    nc = _resolve_nc(input_path)
    prod = _read_emit_netcdf(nc)

    data = prod["data"]
    wl = prod["wavelengths"]
    fwhm = prod["fwhm"]
    good = prod["good_wavelengths"]

    _require(data is not None and data.ndim == 3, "Data cube missing or invalid.")

    source_wavelengths = np.asarray(wl)
    source_fwhm = np.asarray(fwhm) if fwhm is not None else None
    source_good = np.asarray(good, dtype=bool)

    band_validity = [
        bool(np.isfinite(data[:, :, k]).any()) for k in range(data.shape[2])
    ]

    if import_null:
        keep = list(range(data.shape[2]))
    else:
        keep = [k for k in range(data.shape[2]) if source_good[k] and band_validity[k]]

    if not keep:
        gs.fatal("No non-NULL bands found.")

    data = data[:, :, keep]
    wl = np.asarray(wl)[keep]
    if fwhm is not None:
        fwhm = np.asarray(fwhm)[keep]

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

    wkt = gs.read_command("g.proj", flags="wf").strip()
    location_crs = CRS.from_wkt(wkt) if wkt else CRS.from_epsg(4326)
    emit_crs = CRS.from_epsg(4326)

    splat_plan = None
    glt_valid = (prod["glt_y"] > 0) & (prod["glt_x"] > 0)
    ortho_r, ortho_c = np.where(glt_valid)

    if location_crs != emit_crs:
        w_deg = prod["west"]
        e_deg = prod["east"]
        s_deg = prod["south"]
        n_deg = prod["north"]
        ewres_deg = prod["ewres"]
        nsres_deg = prod["nsres"]
        lon_1d = np.linspace(
            w_deg + 0.5 * ewres_deg, e_deg - 0.5 * ewres_deg, prod["ortho_cols"]
        )
        lat_1d = np.linspace(
            n_deg - 0.5 * nsres_deg, s_deg + 0.5 * nsres_deg, prod["ortho_rows"]
        )
        lon2d, lat2d = np.meshgrid(lon_1d, lat_1d)
        lon = lon2d[glt_valid]
        lat = lat2d[glt_valid]
        finite_ll = np.isfinite(lon) & np.isfinite(lat)
        transformer = Transformer.from_crs(emit_crs, location_crs, always_xy=True)
        x, y = transformer.transform(lon, lat)
        x[~finite_ll] = np.nan
        y[~finite_ll] = np.nan
        finite = np.isfinite(x) & np.isfinite(y)
        if not np.any(finite):
            gs.fatal("No valid geolocation points after CRS transform.")
        pixel_size = max(
            float(np.nanmedian(np.abs(np.diff(x)))),
            float(np.nanmedian(np.abs(np.diff(y)))),
        )
        t_west = float(np.nanmin(x[finite])) - 0.5 * pixel_size
        t_east = float(np.nanmax(x[finite])) + 0.5 * pixel_size
        t_south = float(np.nanmin(y[finite])) - 0.5 * pixel_size
        t_north = float(np.nanmax(y[finite])) + 0.5 * pixel_size
        t_cols = max(1, round((t_east - t_west) / pixel_size))
        t_rows = max(1, round((t_north - t_south) / pixel_size))
        fx = (x - t_west) / pixel_size - 0.5
        fy = (t_north - y) / pixel_size - 0.5
        c0 = np.floor(fx).astype(np.int64)
        r0 = np.floor(fy).astype(np.int64)
        dc = fx - c0
        dr = fy - r0
        inb = (
            (c0 >= 0) & (c0 + 1 < t_cols) & (r0 >= 0) & (r0 + 1 < t_rows)
            & finite
        )
        i_inb = np.where(inb)[0]
        splat_plan = {
            "rows": t_rows,
            "cols": t_cols,
            "pixel_size": pixel_size,
            "ri": ortho_r[i_inb],
            "ci": ortho_c[i_inb],
            "r0": r0[i_inb],
            "c0": c0[i_inb],
            "w_ul": ((1 - dr) * (1 - dc))[i_inb],
            "w_ur": ((1 - dr) * dc)[i_inb],
            "w_ll": (dr * (1 - dc))[i_inb],
            "w_lr": (dr * dc)[i_inb],
        }
        gs.info(
            f"Built splat plan: {t_rows}x{t_cols} ({t_rows*t_cols} cells)"
        )
        Module(
            "g.region",
            w=t_west, e=t_east, s=t_south, n=t_north,
            rows=t_rows, cols=t_cols,
            quiet=True,
        )
    else:
        Module(
            "g.region",
            w=prod["west"], e=prod["east"],
            s=prod["south"], n=prod["north"],
            rows=prod["ortho_rows"], cols=prod["ortho_cols"],
            quiet=True,
        )

    def _splat_band(band2d):
        plan = splat_plan
        vals = band2d[plan["ri"], plan["ci"]]
        out = np.zeros((plan["rows"], plan["cols"]), dtype=np.float64)
        wts = np.zeros((plan["rows"], plan["cols"]), dtype=np.float64)
        good = np.isfinite(vals)

        def _scatter(rr, cc, ww):
            m = good & (ww > 0)
            if np.any(m):
                np.add.at(out, (rr[m], cc[m]), vals[m].astype(np.float64) * ww[m])
                np.add.at(wts, (rr[m], cc[m]), ww[m])

        _scatter(plan["r0"], plan["c0"], plan["w_ul"])
        _scatter(plan["r0"], plan["c0"] + 1, plan["w_ur"])
        _scatter(plan["r0"] + 1, plan["c0"], plan["w_ll"])
        _scatter(plan["r0"] + 1, plan["c0"] + 1, plan["w_lr"])

        result = np.full((plan["rows"], plan["cols"]), np.nan, dtype=np.float32)
        nz = wts > 0
        result[nz] = (out[nz] / wts[nz]).astype(np.float32)
        return result

    temp_bands = {}
    created_names = []

    def ensure_band_written(idx1):
        if idx1 in temp_bands:
            return temp_bands[idx1]
        k = idx1 - 1
        ortho2d = _orthorectify_band(data[:, :, k], prod["glt_y"], prod["glt_x"])
        if splat_plan is not None:
            band = _splat_band(ortho2d)
        else:
            band = ortho2d
        name = _temp_name(f"{output_name}_b{idx1:03d}")
        _write_float_raster(name, band)
        temp_bands[idx1] = name
        created_names.append(name)
        return name

    bands_total = int(data.shape[2])
    try:
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
            ortho2d = _orthorectify_band(
                data[:, :, k], prod["glt_y"], prod["glt_x"]
            )
            if splat_plan is not None:
                cube[k, :, :] = _splat_band(ortho2d)
            else:
                cube[k, :, :] = ortho2d

        cube.write(mapname=f"{output_name}", null="nan", overwrite=True)
        gs.info(
            f"Created 3D raster with all bands: {output_name} ({bands_total} slices)."
        )

        try:
            if import_null:
                wavelengths_meta = source_wavelengths.tolist()
                fwhm_meta = source_fwhm.tolist() if source_fwhm is not None else None
                validity_meta = [bool(v) for v in band_validity]
            else:
                wavelengths_meta = wl.tolist()
                fwhm_meta = fwhm.tolist() if fwhm is not None else None
                validity_meta = [True] * len(wavelengths_meta)

            is_radiance = prod.get("data_key") == "radiance"
            meta = HyperMetadata.for_spectral_data(
                wavelengths=wavelengths_meta,
                fwhm=fwhm_meta,
                sensor="EMIT",
                radiometric_quantity=(
                    "at-sensor_radiance" if is_radiance else "surface_reflectance"
                ),
                radiometric_units=(
                    "W/m^2/sr/nm" if is_radiance else "unitless (reflectance)"
                ),
            )
            meta.set_validity(validity_meta)

            _populate_emit_extended_metadata(
                meta=meta,
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
                f"input={shlex.quote(nc)}",
                "product=emit",
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

    import_emit(
        input_path=options["input"],
        output_name=options["output"],
        composites=comps,
        custom_wavelengths=custom,
        strength_val=strength_val,
        import_null=import_null,
    )
