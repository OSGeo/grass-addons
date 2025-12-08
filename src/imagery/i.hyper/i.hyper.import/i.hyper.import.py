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
# % description: Wavelenghts for custom composites
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
# % description: Import also all-NULL bands
# % guisection: Optional
# %end

import sys
import os
import importlib.util
import grass.script as gs
from grass.script.utils import get_lib_path

PRODUCT_MODULE_MAP = {
    "enmap": "enmap",
    "prisma": "prisma",
    "tanager": "tanager",
}


def import_by_product(product, options, flags):
    module_name = PRODUCT_MODULE_MAP.get(product)
    if not module_name:
        gs.fatal(f"Unsupported product: {product}")
    path = get_lib_path(modname="i_hyper_lib", libname=module_name)
    if not path:
        gs.fatal(f"Library path for {module_name} not found.")
    sys.path.append(path)
    spec = importlib.util.find_spec(module_name)
    if not spec:
        gs.fatal(f"Module {module_name} not found at {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(options, flags):
    product = options["product"]
    gs.info(f"Importing product: {product}")
    import_hyper = import_by_product(product, options, flags)
    import_hyper.run_import(options, flags)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main(options, flags))
