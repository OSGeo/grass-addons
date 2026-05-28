#!/usr/bin/env python3
# %module
# % description: Resolve flat areas in a DEM by imposing a local gradient using RichDEM
# % keyword: raster
# % keyword: hydrology
# % keyword: flat areas
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output elevation raster with resolved flats
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
    resolved = rd.ResolveFlats(dem)
    rdarray_to_grass(resolved, options["output"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
