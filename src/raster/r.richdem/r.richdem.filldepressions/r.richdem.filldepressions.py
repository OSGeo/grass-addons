#!/usr/bin/env python3
# %module
# % description: Fill depressions in a DEM using RichDEM
# % keyword: raster
# % keyword: hydrology
# % keyword: depression filling
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output depression-filled elevation raster
# %end
# %option
# % key: topology
# % type: string
# % options: D8,D4
# % answer: D8
# % description: Flow topology
# %end
# %flag
# % key: e
# % description: Apply epsilon gradient to flat areas after filling
# %end

import sys
import grass.script as gs


def main():
    options, flags = gs.parser()

    from grass.script.utils import get_lib_path

    path = get_lib_path(modname="r.richdem", libname="librichdem")
    if path is None:
        gs.fatal("librichdem not found. Is r.richdem fully installed?")
    sys.path.insert(0, path)
    from librichdem.raster import rdarray_from_grass, rdarray_to_grass

    import richdem as rd

    dem = rdarray_from_grass(options["input"])
    filled = rd.FillDepressions(dem, epsilon=flags["e"], topology=options["topology"])
    rdarray_to_grass(filled, options["output"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
