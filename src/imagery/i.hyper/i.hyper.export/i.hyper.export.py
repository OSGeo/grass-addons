#!/usr/bin/env python

##############################################################################
# MODULE:    i.hyper.export
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Export 3D hyperspectral raster map.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Export 3D hyperspectral raster map as multi-band GeoTIFF, HDF5, Zarr, or native .ihyper gzip archive.
# % keyword: raster3d
# % keyword: export
# % keyword: output
# % keyword: voxel
# %end

# %option G_OPT_R3_INPUT
# % required: yes
# % description: Input 3D raster map
# % guisection: Input
# %end

# %option G_OPT_F_OUTPUT
# % required: yes
# % description: Output file name
# % guisection: Output
# %end

# %option
# % key: format
# % type: string
# % required: no
# % multiple: no
# % options: gtiff,ihyper,h5,zarr
# % answer: ihyper
# % description: Export format
# % guisection: Output
# %end

# %option
# % key: chunks
# % type: string
# % required: no
# % multiple: no
# % answer: 0,0,0
# % description: Chunk sizes in band,row,col order (first value is the spectral axis; used only for h5 and zarr, 0 = automatic)
# % guisection: Output
# %end

# %flag
# % key: c
# % description: Include existing related composites in .ihyper export
# % guisection: Output
# %end

import json
import os
from pathlib import Path
import shutil
import sys
import tarfile
import tempfile

import numpy as np

import grass.script as gs
import grass.script.array as garray


RASTER_ELEMENTS = ("cell", "fcell", "cellhd", "cats", "colr", "hist")
RASTER_MISC_DIR = "cell_misc"
GTIFF_NODATA = -9999.0


def _mapset_path(mapset=None):
    env = gs.gisenv()
    if mapset is None:
        mapset = env["MAPSET"]
    return Path(env["GISDBASE"]) / env["LOCATION_NAME"] / mapset


def _grid3_map_path(map_name, mapset=None):
    return _mapset_path(mapset) / "grid3" / map_name


def _validate_hyper_map(map_name):
    found = gs.find_file(map_name, element="grid3")
    if not found.get("fullname"):
        gs.fatal(f"3D raster map '{map_name}' not found.")


def _copy_tree(src, dst):
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def _list_related_composites(base_name):
    result = gs.read_command(
        "g.list", type="raster", pattern=f"{base_name}_*", flags="m"
    )
    names = [line.strip() for line in result.splitlines() if line.strip()]
    return sorted(set(name.split("@")[0] for name in names))


def _copy_raster_support(mapset_path, raster_name, export_root):
    copied = []
    for element in RASTER_ELEMENTS:
        src = mapset_path / element / raster_name
        if src.exists():
            dst = export_root / "raster" / element / raster_name
            _copy_tree(src, dst)
            copied.append(str(Path("raster") / element / raster_name))

    misc_src = mapset_path / RASTER_MISC_DIR / raster_name
    if misc_src.exists():
        dst = export_root / "raster" / RASTER_MISC_DIR / raster_name
        _copy_tree(misc_src, dst)
        copied.append(str(Path("raster") / RASTER_MISC_DIR / raster_name))

    return copied


def _normalize_output_path(output_file, export_format):
    output_path = Path(output_file)
    suffix_map = {"ihyper": ".ihyper", "h5": ".h5", "zarr": ".zarr"}
    wanted = suffix_map.get(export_format)
    if not wanted:
        return output_path
    if output_path.suffix.lower() == wanted:
        return output_path
    if output_path.suffix:
        return output_path.with_suffix(output_path.suffix + wanted)
    return output_path.with_suffix(wanted)


def _dms_to_decimal(dms_str):
    parts = dms_str.strip().split(":")
    if len(parts) != 3:
        raise ValueError
    deg, mins, secs = float(parts[0]), float(parts[1]), float(parts[2])
    if deg < 0:
        return deg - mins / 60 - secs / 3600
    return deg + mins / 60 + secs / 3600


def _normalize_r3_info(map_name):
    info = gs.parse_command("r3.info", map=map_name, flags="g")
    normalized = {}
    numeric_keys = {
        "north",
        "south",
        "east",
        "west",
        "bottom",
        "top",
        "nsres",
        "ewres",
        "tbres",
        "rows",
        "cols",
        "depths",
        "tilenumx",
        "tilenumy",
        "tilenumz",
        "tiledimx",
        "tiledimy",
        "tiledimz",
    }
    for key, value in info.items():
        clean = value.strip('"') if isinstance(value, str) else value
        if key in numeric_keys:
            try:
                normalized[key] = int(clean)
            except (ValueError, TypeError):
                try:
                    normalized[key] = float(clean)
                except (ValueError, TypeError):
                    normalized[key] = _dms_to_decimal(clean)
        else:
            normalized[key] = clean
    return normalized


def _load_hyper_metadata(input_3d):
    metadata_path = _grid3_map_path(input_3d) / "hyper.json"
    if not metadata_path.exists():
        gs.fatal(f"Metadata file not found for '{input_3d}': {metadata_path}")
    with open(metadata_path, "r", encoding="utf-8") as file_obj:
        return json.load(file_obj)


def _get_projection_wkt():
    try:
        return gs.read_command("g.proj", flags="wf", quiet=True).strip()
    except gs.CalledModuleError:
        return ""


def _build_export_metadata(input_3d):
    input_name = input_3d.split("@")[0]
    hyper = _load_hyper_metadata(input_name)
    info = _normalize_r3_info(input_3d)

    transform = [
        info["west"],
        info["ewres"],
        0.0,
        info["north"],
        0.0,
        -info["nsres"],
    ]
    bounds = {
        "west": info["west"],
        "east": info["east"],
        "south": info["south"],
        "north": info["north"],
        "bottom": info["bottom"],
        "top": info["top"],
    }
    resolution = {
        "nsres": info["nsres"],
        "ewres": info["ewres"],
        "tbres": info["tbres"],
    }

    return {
        "input": input_3d,
        "input_name": input_name,
        "hyper": hyper,
        "hyper_json": json.dumps(hyper, indent=2, sort_keys=True),
        "grid3_info": info,
        "grid3_info_json": json.dumps(info, indent=2, sort_keys=True),
        "projection_wkt": _get_projection_wkt(),
        "axis_order": ["band", "row", "col"],
        "shape": [info["depths"], info["rows"], info["cols"]],
        "bounds": bounds,
        "resolution": resolution,
        "transform": transform,
        "bands": hyper.get("bands", {}),
    }


def _parse_chunks(chunk_text, shape):
    parts = [part.strip() for part in (chunk_text or "0,0,0").split(",")]
    if len(parts) != 3:
        gs.fatal("chunks must be three comma-separated integers in band,row,col order")

    try:
        requested = [int(part) for part in parts]
    except ValueError:
        gs.fatal("chunks must be three comma-separated integers in band,row,col order")

    if any(value < 0 for value in requested):
        gs.fatal("chunks values must be non-negative integers")

    defaults = [min(shape[0], 16), min(shape[1], 256), min(shape[2], 256)]
    resolved = []
    for idx, value in enumerate(requested):
        size = defaults[idx] if value == 0 else value
        size = max(1, min(int(size), int(shape[idx])))
        resolved.append(size)
    return tuple(resolved)


def _safe_numeric_array(values, dtype=np.float32):
    if values is None:
        return None
    cleaned = [np.nan if value is None else value for value in values]
    return np.asarray(cleaned, dtype=dtype)


def _create_slices(input_3d_full):
    input_name = input_3d_full.split("@")[0]
    base = f"{input_name}_slice_{os.getpid()}"

    gs.use_temp_region()
    try:
        gs.run_command("g.region", raster_3d=input_3d_full, quiet=True)
        gs.run_command("r3.to.rast", input=input_3d_full, output=base, quiet=True)
        raster_list = gs.read_command(
            "g.list", type="raster", pattern=f"{base}_*", flags="m"
        )
        rasters = [line.strip() for line in raster_list.splitlines() if line.strip()]

        def _index(rname):
            name = rname.split("@")[0]
            return int(name[len(base) + 1 :])

        rasters = sorted(rasters, key=_index)
        if not rasters:
            gs.fatal(f"No valid slice maps found with base name {base}_*")
        return rasters
    except Exception:
        gs.del_temp_region()
        raise


def _cleanup_slices(raster_list, group_name=None):
    try:
        if raster_list:
            gs.run_command(
                "g.remove", type="raster", name=raster_list, flags="f", quiet=True
            )
        if group_name:
            gs.run_command(
                "g.remove", type="group", name=group_name, flags="f", quiet=True
            )
    finally:
        gs.del_temp_region()


def _stack_cube(raster_list):
    cube = []
    for raster in raster_list:
        layer = np.asarray(garray.array(raster, null=np.nan), dtype=np.float32)
        cube.append(layer)
    return np.stack(cube, axis=0)


def _write_gtiff_metadata(output_file, meta):
    try:
        from osgeo import gdal
    except ImportError as error:
        gs.warning(
            f"GDAL Python bindings not available, skipping GeoTIFF metadata write: {error}"
        )
        return

    dataset = gdal.OpenEx(str(output_file), gdal.OF_RASTER | gdal.OF_UPDATE)
    if dataset is None:
        gs.warning(f"Could not reopen GeoTIFF for metadata update: {output_file}")
        return

    bands = meta["bands"]
    dataset_meta = {
        "IHYPER_SCHEMA_VERSION": str(meta["hyper"].get("schema_version", "")),
        "IHYPER_DATASET_ID": str(meta["hyper"].get("dataset_id", "")),
        "IHYPER_SENSOR": str(meta["hyper"].get("sensor", "") or ""),
        "IHYPER_DATA_TYPE": str(meta["hyper"].get("data_type", "") or ""),
        "IHYPER_WAVELENGTH_UNITS": str(meta["hyper"].get("wavelength_units", "") or ""),
        "IHYPER_RADIOMETRIC_QUANTITY": str(
            meta["hyper"].get("radiometric_quantity", "") or ""
        ),
        "IHYPER_RADIOMETRIC_UNITS": str(
            meta["hyper"].get("radiometric_units", "") or ""
        ),
        "IHYPER_AXIS_ORDER": "band,row,col",
        "IHYPER_HYPER_JSON": meta["hyper_json"],
        "IHYPER_GRID3_INFO_JSON": meta["grid3_info_json"],
    }
    dataset.SetMetadata(dataset_meta)

    wavelengths = bands.get("wavelength") or []
    fwhm = bands.get("fwhm") or []
    validity = bands.get("validity") or []

    for index in range(dataset.RasterCount):
        band = dataset.GetRasterBand(index + 1)
        band.SetDescription(f"Band {index + 1:03d}")
        band_meta = {
            "band_index": str(index + 1),
            "validity": str(bool(validity[index])) if index < len(validity) else "",
            "wavelength": ""
            if index >= len(wavelengths) or wavelengths[index] is None
            else str(wavelengths[index]),
            "fwhm": ""
            if index >= len(fwhm) or fwhm[index] is None
            else str(fwhm[index]),
            "wavelength_units": str(meta["hyper"].get("wavelength_units", "") or ""),
        }
        band.SetMetadata(band_meta, "IHYPER")

    dataset.FlushCache()
    dataset = None


def _export_native_archive(input_3d_full, output_file, include_composites):
    input_3d = input_3d_full.split("@")[0]
    _validate_hyper_map(input_3d)

    mapset_path = _mapset_path()
    grid3_src = _grid3_map_path(input_3d)
    hyper_json = grid3_src / "hyper.json"
    if not hyper_json.exists():
        gs.fatal(f"Metadata file not found for '{input_3d_full}': {hyper_json}")

    archive_path = _normalize_output_path(output_file, "ihyper")
    composite_files = {}

    with tempfile.TemporaryDirectory(prefix="ihyper_export_") as tmpdir:
        tmp_root = Path(tmpdir)
        _copy_tree(grid3_src, tmp_root / "grid3" / input_3d)

        if include_composites:
            composites = _list_related_composites(input_3d)
            for name in composites:
                copied = _copy_raster_support(mapset_path, name, tmp_root)
                if copied:
                    composite_files[name] = copied

        manifest = {
            "format": "ihyper",
            "compression": "gzip",
            "map_name": input_3d,
            "mapset": gs.gisenv()["MAPSET"],
            "location": gs.gisenv()["LOCATION_NAME"],
            "has_metadata": True,
            "composites_included": bool(include_composites and composite_files),
            "composites": sorted(composite_files),
            "composite_files": composite_files,
        }
        (tmp_root / "manifest.json").write_text(
            json.dumps(manifest, indent=2), encoding="utf-8"
        )

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(tmp_root / "manifest.json", arcname="manifest.json")
            tar.add(tmp_root / "grid3", arcname="grid3")
            if composite_files:
                tar.add(tmp_root / "raster", arcname="raster")

    gs.message(f"Exported {input_3d_full} to {archive_path} as native .ihyper archive")


def _export_gtiff(input_3d_full, output_file, meta):
    output_path = Path(output_file)
    raster_list = []
    group_name = f"{meta['input_name']}_export_group_{os.getpid()}"

    try:
        raster_list = _create_slices(input_3d_full)
        gs.run_command(
            "i.group", group=group_name, input=",".join(raster_list), quiet=True
        )
        gs.run_command(
            "g.region", raster=raster_list[0], align=raster_list[0], quiet=True
        )
        gs.run_command(
            "r.out.gdal",
            input=group_name,
            output=str(output_path),
            format="GTiff",
            createopt="COMPRESS=DEFLATE,PREDICTOR=3,BIGTIFF=YES,INTERLEAVE=BAND",
            nodata=GTIFF_NODATA,
            flags="c",
            overwrite=True,
            superquiet=True,
        )
    finally:
        _cleanup_slices(raster_list, group_name)

    _write_gtiff_metadata(output_path, meta)
    gs.message(f"Exported {input_3d_full} to {output_path} as multi-band GeoTIFF")


def _write_h5_metadata(h5file, meta):
    import h5py

    meta_group = h5file.require_group("metadata")
    bands_group = h5file.require_group("bands")

    string_dtype = h5py.string_dtype(encoding="utf-8")
    meta_group.create_dataset("hyper_json", data=meta["hyper_json"], dtype=string_dtype)
    meta_group.create_dataset(
        "grid3_info_json", data=meta["grid3_info_json"], dtype=string_dtype
    )
    meta_group.attrs["axis_order"] = "band,row,col"
    meta_group.attrs["projection_wkt"] = meta["projection_wkt"]
    meta_group.attrs["transform"] = meta["transform"]
    meta_group.attrs["shape"] = meta["shape"]
    meta_group.attrs["bounds_json"] = json.dumps(meta["bounds"], sort_keys=True)
    meta_group.attrs["resolution_json"] = json.dumps(meta["resolution"], sort_keys=True)

    bands = meta["bands"]
    wavelengths = _safe_numeric_array(bands.get("wavelength"))
    fwhm = _safe_numeric_array(bands.get("fwhm"))
    validity = np.asarray(bands.get("validity") or [], dtype=np.uint8)

    if wavelengths is not None:
        bands_group.create_dataset("wavelength", data=wavelengths)
    if fwhm is not None:
        bands_group.create_dataset("fwhm", data=fwhm)
    if len(validity):
        bands_group.create_dataset("validity", data=validity)


def _export_h5(input_3d_full, output_file, meta, chunks_option):
    try:
        import h5py
    except ImportError as error:
        gs.fatal(f"h5 export requires h5py: {error}")

    output_path = _normalize_output_path(output_file, "h5")
    raster_list = []
    try:
        raster_list = _create_slices(input_3d_full)
        cube = _stack_cube(raster_list)
    finally:
        _cleanup_slices(raster_list)

    chunks = _parse_chunks(chunks_option, cube.shape)
    with h5py.File(output_path, "w") as h5file:
        dataset = h5file.create_dataset(
            "cube",
            data=cube,
            chunks=chunks,
            compression="gzip",
            shuffle=True,
        )
        dataset.attrs["axis_order"] = "band,row,col"
        dataset.attrs["spectral_axis"] = 0
        dataset.attrs["chunk_order"] = "band,row,col"
        dataset.attrs["nodata"] = np.nan
        _write_h5_metadata(h5file, meta)

    gs.message(
        f"Exported {input_3d_full} to {output_path} as HDF5 cube with shape {cube.shape}"
    )


def _export_zarr(input_3d_full, output_file, meta, chunks_option):
    try:
        import zarr
    except ImportError as error:
        gs.fatal(f"zarr export requires the zarr Python package: {error}")

    output_path = _normalize_output_path(output_file, "zarr")
    raster_list = []
    try:
        raster_list = _create_slices(input_3d_full)
        cube = _stack_cube(raster_list)
    finally:
        _cleanup_slices(raster_list)

    chunks = _parse_chunks(chunks_option, cube.shape)
    root = zarr.open_group(str(output_path), mode="w")
    root.create_array("cube", data=cube, chunks=chunks, overwrite=True)
    root["cube"].attrs.update(
        {
            "axis_order": "band,row,col",
            "spectral_axis": 0,
            "chunk_order": "band,row,col",
            "nodata": "nan",
        }
    )

    meta_group = root.require_group("metadata")
    meta_group.attrs.update(
        {
            "axis_order": "band,row,col",
            "projection_wkt": meta["projection_wkt"],
            "transform": meta["transform"],
            "shape": meta["shape"],
            "bounds_json": json.dumps(meta["bounds"], sort_keys=True),
            "resolution_json": json.dumps(meta["resolution"], sort_keys=True),
            "hyper_json": meta["hyper_json"],
            "grid3_info_json": meta["grid3_info_json"],
        }
    )

    bands_group = root.require_group("bands")
    wavelengths = _safe_numeric_array(meta["bands"].get("wavelength"))
    fwhm = _safe_numeric_array(meta["bands"].get("fwhm"))
    validity = np.asarray(meta["bands"].get("validity") or [], dtype=np.uint8)
    if wavelengths is not None:
        bands_group.create_array("wavelength", data=wavelengths, overwrite=True)
    if fwhm is not None:
        bands_group.create_array("fwhm", data=fwhm, overwrite=True)
    if len(validity):
        bands_group.create_array("validity", data=validity, overwrite=True)

    gs.message(
        f"Exported {input_3d_full} to {output_path} as Zarr cube with shape {cube.shape}"
    )


def main():
    options, flags = gs.parser()
    input_3d_full = options["input"]
    output_file = options["output"]
    export_format = options["format"]
    chunks_option = options["chunks"]

    input_name = input_3d_full.split("@")[0]
    _validate_hyper_map(input_name)

    if export_format == "ihyper":
        _export_native_archive(
            input_3d_full, output_file, include_composites=bool(flags.get("c"))
        )
        return

    meta = _build_export_metadata(input_3d_full)

    if export_format == "gtiff":
        _export_gtiff(input_3d_full, output_file, meta)
    elif export_format == "h5":
        _export_h5(input_3d_full, output_file, meta, chunks_option)
    elif export_format == "zarr":
        _export_zarr(input_3d_full, output_file, meta, chunks_option)
    else:
        gs.fatal(f"Unsupported export format: {export_format}")


if __name__ == "__main__":
    sys.exit(main())
