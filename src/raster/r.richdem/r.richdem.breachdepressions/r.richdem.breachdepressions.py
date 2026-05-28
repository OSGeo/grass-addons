#!/usr/bin/env python3
# %module
# % description: Breach depressions in a DEM using RichDEM
# % keyword: raster
# % keyword: hydrology
# % keyword: depression breaching
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output depression-breached elevation raster
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
# % description: Use Lindsay2016 epsilon-gradient shallowing (pit raised to just below lowest neighbour rather than exactly to it)
# %end

import sys
import grass.script as gs
from grass.pygrass.utils import get_lib_path


def main():
    options, flags = gs.parser()

    path = get_lib_path(modname="r.richdem", libname="librichdem")
    if path is None:
        gs.fatal("librichdem not found. Is r.richdem fully installed?")
    sys.path.insert(0, path)
    from librichdem.raster import rdarray_from_grass, rdarray_to_grass

    import richdem as rd

    dem = rdarray_from_grass(options["input"])

    if flags["e"]:
        if not hasattr(rd, "BreachDepressionsEps"):
            gs.fatal(
                "Lindsay2016 epsilon-gradient breaching (BreachDepressionsEps) is "
                "not available in this RichDEM build. A patch exposing this function "
                "via the Python bindings is needed upstream."
            )
        if options["topology"] == "D4":
            gs.fatal(
                "Lindsay2016 (flag -e) does not support D4 topology; "
                "only D8 is available."
            )
        breached = rd.BreachDepressionsEps(dem)
    else:
        breached = rd.BreachDepressions(dem, topology=options["topology"])

    rdarray_to_grass(breached, options["output"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
