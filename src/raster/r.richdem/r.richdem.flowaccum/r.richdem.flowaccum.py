#!/usr/bin/env python3
# %module
# % description: Calculate flow accumulation using RichDEM
# % keyword: raster
# % keyword: hydrology
# % keyword: flow accumulation
# % keyword: flow direction
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output flow accumulation raster
# %end
# %option
# % key: method
# % type: string
# % options: D8,D4,Dinf,Tarboton,Quinn,Holmgren,Freeman,Rho8,Rho4,FairfieldLeymarieD8,FairfieldLeymarieD4,OCallaghanD8,OCallaghanD4
# % answer: D8
# % description: Flow accumulation method
# %end
# %option
# % key: exponent
# % type: double
# % required: no
# % description: Exponent for Holmgren or Freeman methods
# %end
# %option G_OPT_R_INPUT
# % key: weights
# % required: no
# % description: Optional flow accumulation weights raster
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
    exponent = float(options["exponent"]) if options["exponent"] else None
    weights = rdarray_from_grass(options["weights"]) if options["weights"] else None

    accum = rd.FlowAccumulation(dem, method=options["method"], exponent=exponent, weights=weights)
    rdarray_to_grass(accum, options["output"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
