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
# % options: prisma, enmap, tanager
# % answer: prisma
# % description: Define the hyperspectral product you want to import (lowercase).
# % guisection: Input
# %end

# %option G_OPT_R3_OUTPUT
# % required: yes
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


def _safe_extract_ihyper(input_path, output_name):
    archive_path = Path(input_path)
    if archive_path.suffix.lower() != ".ihyper":
        return False

    mapset_path = _mapset_path()
    grid3_root = mapset_path / "grid3"
    grid3_root.mkdir(parents=True, exist_ok=True)

    with tarfile.open(archive_path, "r:gz") as tar:
        names = tar.getnames()
        if "manifest.json" not in names:
            gs.fatal("Invalid .ihyper archive: manifest.json missing.")

        manifest_member = tar.extractfile("manifest.json")
        if manifest_member is None:
            gs.fatal("Invalid .ihyper archive: cannot read manifest.json.")
        manifest = json.load(manifest_member)
        archived_name = manifest.get("map_name")
        if not archived_name:
            gs.fatal("Invalid .ihyper archive: map_name missing in manifest.")

        expected_prefix = f"grid3/{archived_name}/"
        members = [m for m in tar.getmembers() if m.name.startswith(expected_prefix)]
        if not members:
            gs.fatal(f"Invalid .ihyper archive: {expected_prefix} missing.")

        target_path = grid3_root / archived_name
        if target_path.exists():
            gs.fatal(f"Target 3D raster '{archived_name}' already exists in current mapset.")

        with tempfile.TemporaryDirectory(prefix="ihyper_import_") as tmpdir:
            tmp_root = Path(tmpdir)
            for member in members:
                rel = Path(member.name).relative_to("grid3")
                dest = tmp_root / rel
                if member.isdir():
                    dest.mkdir(parents=True, exist_ok=True)
                    continue
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tar.extractfile(member) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)

            restored = tmp_root / archived_name
            if not (restored / "hyper.json").exists():
                gs.fatal("Invalid .ihyper archive: hyper.json missing in grid3 map directory.")
            shutil.move(str(restored), str(target_path))

    if output_name and output_name != archived_name:
        gs.warning(
            f"Output name '{output_name}' ignored for .ihyper import; restored archive map '{archived_name}'."
        )

    gs.message(f"Imported native hyperspectral archive {archive_path} as {archived_name}")
    return True


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
    if _safe_extract_ihyper(options["input"], options.get("output")):
        return

    product = options["product"]
    gs.info(f"Importing product: {product}")
    import_hyper = import_by_product(product, options, flags)
    import_hyper.run_import(options, flags)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main(options, flags))
