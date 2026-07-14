#!/usr/bin/env python
##############################################################################
# MODULE:    i.hyper.import
# AUTHOR(S): Alen Mangafic and Tomaž Žagar, Geodetic Institute of Slovenia
# PURPOSE:   Hyperspectral imagery import.
# COPYRIGHT: (C) 2025 by Alen Mangafic and the GRASS Development Team
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % description: Hyperspectral imagery import.
# % keyword: imagery
# % keyword: import
# %end

# %option G_OPT_F_INPUT
# % required: yes
# % description: Path to the hyperspectral imagery: pick any file if the product is multi-file.
# % guisection: Input
# %end

# %option
# % key: product
# % type: string
# % required: yes
# % multiple: no
# % options: prisma, enmap, tanager, ihyper
# % answer: prisma
# % description: Define the hyperspectral product you want to import (lowercase).
# % guisection: Input
# %end

# %option G_OPT_R3_OUTPUT
# % required: no
# % description: Set the name of the output hyperspectral 3D raster map.
# % guisection: Input
# %end

# %option
# % key: composites
# % type: string
# % required: no
# % multiple: yes
# % options: rgb,cir,swir_agriculture,swir_geology
# % description: Composites to generate during import
# % guisection: Optional
# %end

# %option
# % key: composites_custom
# % type: string
# % description: Wavelengths for custom composites
# % guisection: Optional
# %end

# %option
# % key: strength
# % type: integer
# % required: no
# % answer: 96
# % description: Cropping intensity - upper brightness level (0-100)
# % guisection: Optional
# %end

# %flag
# % key: n
# % description: Record full source-band validity in bands.validity (do not add NULL bands to raster_3d)
# % guisection: Optional
# %end

# %flag
# % key: p
# % description: Print dataset spatial reference, i.hyper.import behavior, and project requirements, then exit
# % guisection: Optional
# %end

import sys
import os
import importlib.util
import json
from pathlib import Path
import shutil
import tarfile
import tempfile
import grass.script as gs
from grass.script.utils import get_lib_path

PRODUCT_MODULE_MAP = {
    "enmap": "enmap",
    "prisma": "prisma",
    "tanager": "tanager",
}


def _mapset_path():
    env = gs.gisenv()
    return Path(env["GISDBASE"]) / env["LOCATION_NAME"] / env["MAPSET"]


def _is_safe_archive_member_name(name):
    path = Path(name)
    return not path.is_absolute() and ".." not in path.parts


def _manifest_composite_members(manifest):
    composite_files = manifest.get("composite_files") or {}
    if not isinstance(composite_files, dict):
        gs.fatal("Invalid native archive: composite_files in manifest must be a dict.")

    members = set()
    for archived_paths in composite_files.values():
        if not isinstance(archived_paths, list):
            gs.fatal(
                "Invalid native archive: composite_files entries must be path lists."
            )
        for archived_path in archived_paths:
            if not isinstance(archived_path, str):
                gs.fatal(
                    "Invalid native archive: composite_files entries must be strings."
                )
            clean = archived_path.rstrip("/")
            if (
                not clean.startswith("raster/")
                or not _is_safe_archive_member_name(clean)
                or len(Path(clean).parts) < 3
            ):
                gs.fatal(
                    "Invalid native archive: unsafe composite path in manifest: "
                    f"'{archived_path}'."
                )
            members.add(clean)
    return members


def _open_ihyper_archive(input_path):
    archive_path = Path(input_path)
    try:
        tar = tarfile.open(archive_path, "r:gz")
    except (tarfile.TarError, OSError) as error:
        gs.fatal(f"Input file is not a valid native i.hyper archive: {error}")

    names = tar.getnames()
    if "manifest.json" not in names:
        tar.close()
        gs.fatal("Invalid native archive: manifest.json missing.")

    manifest_member = tar.extractfile("manifest.json")
    if manifest_member is None:
        tar.close()
        gs.fatal("Invalid native archive: cannot read manifest.json.")

    try:
        manifest = json.load(manifest_member)
    except json.JSONDecodeError as error:
        tar.close()
        gs.fatal(f"Invalid native archive: manifest.json is not valid JSON: {error}")

    archived_name = manifest.get("map_name")
    if not archived_name:
        tar.close()
        gs.fatal("Invalid native archive: map_name missing in manifest.")
    if not gs.legal_name(archived_name):
        tar.close()
        gs.fatal(f"Invalid native archive: illegal map_name '{archived_name}'.")

    expected_root = f"grid3/{archived_name}"
    composite_members = _manifest_composite_members(manifest)
    members = []
    for member in tar.getmembers():
        name = member.name.rstrip("/")
        if not _is_safe_archive_member_name(name):
            tar.close()
            gs.fatal(f"Invalid native archive: unsafe member path '{member.name}'.")

        include = name == expected_root or name.startswith(f"{expected_root}/")
        if not include:
            include = any(
                name == root or name.startswith(f"{root}/")
                for root in composite_members
            )
        if include:
            members.append(member)

    if not members:
        tar.close()
        gs.fatal(f"Invalid native archive: {expected_root}/ missing.")

    return tar, manifest, archived_name, members, composite_members


def _safe_extract_ihyper(input_path, output_name):
    archive_path = Path(input_path)
    tar, _manifest, archived_name, members, composite_members = _open_ihyper_archive(
        input_path
    )

    mapset_path = _mapset_path()
    grid3_root = mapset_path / "grid3"
    grid3_root.mkdir(parents=True, exist_ok=True)

    target_path = grid3_root / archived_name
    if target_path.exists():
        tar.close()
        gs.fatal(
            f"Target 3D raster '{archived_name}' already exists in current mapset."
        )

    with tempfile.TemporaryDirectory(prefix="ihyper_import_") as tmpdir:
        tmp_root = Path(tmpdir)
        tmp_root_resolved = tmp_root.resolve()
        for member in members:
            if not (member.isdir() or member.isfile()):
                tar.close()
                gs.fatal(
                    f"Invalid native archive: unsupported member type '{member.name}'."
                )
            member_path = Path(member.name.rstrip("/"))
            dest = tmp_root / member_path
            if tmp_root_resolved not in dest.resolve().parents and (
                dest.resolve() != tmp_root_resolved
            ):
                tar.close()
                gs.fatal(
                    "Invalid native archive: member escapes extraction root: "
                    f"'{member.name}'."
                )
            if member.isdir():
                dest.mkdir(parents=True, exist_ok=True)
                continue
            dest.parent.mkdir(parents=True, exist_ok=True)
            extracted = tar.extractfile(member)
            if extracted is None:
                tar.close()
                gs.fatal(f"Invalid native archive: cannot read member '{member.name}'.")
            with extracted as src, open(dest, "wb") as dst:
                shutil.copyfileobj(src, dst)

        restored = tmp_root / "grid3" / archived_name
        if not (restored / "hyper.json").exists():
            tar.close()
            gs.fatal(
                "Invalid native archive: hyper.json missing in grid3 map directory."
            )
        shutil.move(str(restored), str(target_path))

        for member_name in sorted(composite_members):
            source = tmp_root / member_name
            if not source.exists():
                tar.close()
                gs.fatal(
                    "Invalid native archive: manifest references missing member "
                    f"'{member_name}'."
                )
            target = mapset_path / Path(member_name).relative_to("raster")
            if target.exists():
                gs.warning(
                    f"Skipping existing raster support path during import: {target}"
                )
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if source.is_dir():
                shutil.copytree(source, target)
            else:
                shutil.copy2(source, target)

    tar.close()

    if output_name and output_name != archived_name:
        gs.warning(
            f"Output name '{output_name}' ignored for native import; restored archive map '{archived_name}'."
        )

    gs.message(
        f"Imported native hyperspectral archive {archive_path} as {archived_name}"
    )


def import_by_product(product, options, flags):
    module_name = PRODUCT_MODULE_MAP.get(product)
    if not module_name:
        gs.fatal(f"Unsupported product: {product}")
    path = get_lib_path(modname="i_hyper_lib", libname=module_name)
    if not path:
        gs.fatal(f"Library path for {module_name} not found.")
    module_file = os.path.join(path, f"{module_name}.py")
    if not os.path.exists(module_file):
        gs.fatal(f"Module file not found: {module_file}")
    if path not in sys.path:
        sys.path.append(path)
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if not spec or not spec.loader:
        gs.fatal(f"Failed to load module spec from {module_file}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(module_name, None)
        raise
    return module


def main(options, flags):
    product = options["product"]
    output = options.get("output")

    path = get_lib_path(modname="i_hyper_lib", libname="check_proj")
    if path and path not in sys.path:
        sys.path.append(path)
    import check_proj

    if product == "enmap":
        import_hyper = import_by_product(product, options, flags)
        options["input"] = import_hyper._resolve_enmap_dir(options["input"])

    if flags.get("p"):
        if product == "ihyper":
            gs.fatal("The -p flag is not supported for product=ihyper.")
        check_proj.print_proj_info(product, options["input"])
        return

    if product == "ihyper":
        _safe_extract_ihyper(options["input"], output)
        return

    if not output:
        gs.fatal(
            "Parameter <output> is required. "
            "Set the name of the output hyperspectral 3D raster map."
        )

    check_proj.check_import_allowed(product, options["input"])

    gs.info(f"Importing product: {product}")
    import_hyper = import_by_product(product, options, flags)
    import_hyper.run_import(options, flags)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main(options, flags))
