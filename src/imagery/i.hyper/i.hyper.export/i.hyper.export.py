#!/usr/bin/env python

##############################################################################
# MODULE:    i.hyper.export
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Export 3D hyperspectral raster map.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Export 3D hyperspectral raster map as multi-band GeoTIFF or native .ihyper gzip archive.
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
# % options: gtiff,ihyper
# % answer: gtiff
# % description: Export format
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

import grass.script as gs


RASTER_ELEMENTS = ("cell", "fcell", "cellhd", "cats", "colr", "hist")
RASTER_MISC_DIR = "cell_misc"


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
    result = gs.read_command("g.list", type="raster", pattern=f"{base_name}_*", flags="m")
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


def _export_native_archive(input_3d_full, output_file, include_composites):
    input_3d = input_3d_full.split("@")[0]
    _validate_hyper_map(input_3d)

    mapset_path = _mapset_path()
    grid3_src = _grid3_map_path(input_3d)
    hyper_json = grid3_src / "hyper.json"
    if not hyper_json.exists():
        gs.fatal(f"Metadata file not found for '{input_3d_full}': {hyper_json}")

    archive_path = Path(output_file)
    if archive_path.suffix != ".ihyper":
        archive_path = archive_path.with_suffix(archive_path.suffix + ".ihyper") if archive_path.suffix else archive_path.with_suffix(".ihyper")

    composites = []
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
        (tmp_root / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(tmp_root / "manifest.json", arcname="manifest.json")
            tar.add(tmp_root / "grid3", arcname="grid3")
            if composite_files:
                tar.add(tmp_root / "raster", arcname="raster")

    gs.message(f"Exported {input_3d_full} to {archive_path} as native .ihyper archive")


def _export_gtiff(input_3d_full, output_file):
    input_3d = input_3d_full.split("@")[0]
    base = f"{input_3d}_slice"

    gs.run_command("g.region", raster_3d=input_3d_full)
    gs.run_command("r3.to.rast", input=input_3d_full, output=base, quiet=True)

    raster_list = gs.parse_command("g.list", type="raster", pattern=f"{base}_*", flags="m")

    def _get_index(rname):
        r = rname.split("@")[0]
        return int(r[len(base) + 1 :])

    raster_list = sorted(raster_list, key=_get_index)
    if not raster_list:
        gs.fatal(f"No valid slice maps found with base name {base}_*")

    group_name = f"{input_3d}_export_group"
    gs.run_command("i.group", group=group_name, input=",".join(raster_list), quiet=True)
    gs.run_command("g.region", raster=raster_list[0], align=raster_list[0], quiet=True)

    gs.run_command(
        "r.out.gdal",
        input=group_name,
        output=output_file,
        format="GTiff",
        createopt="COMPRESS=DEFLATE,PREDICTOR=3,BIGTIFF=YES,INTERLEAVE=BAND",
        nodata=-9999,
        flags="c",
        overwrite=True,
        superquiet=True,
    )

    gs.run_command("g.remove", type="raster", name=raster_list, flags="f", quiet=True)
    gs.run_command("g.remove", type="group", name=group_name, flags="f", quiet=True)
    gs.message(f"Exported {input_3d_full} to {output_file} as multi-band GeoTIFF")


def main():
    options, flags = gs.parser()
    input_3d_full = options["input"]
    output_file = options["output"]
    export_format = options["format"]

    if export_format == "ihyper":
        _export_native_archive(input_3d_full, output_file, include_composites=bool(flags.get("c")))
    else:
        _export_gtiff(input_3d_full, output_file)


if __name__ == "__main__":
    sys.exit(main())
