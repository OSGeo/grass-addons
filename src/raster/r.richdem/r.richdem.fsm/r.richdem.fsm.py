#!/usr/bin/env python3
# %module
# % description: Apply one Fill-Spill-Merge step to redistribute surface water using RichDEM
# % keyword: raster
# % keyword: vector
# % keyword: hydrology
# % keyword: fill-spill-merge
# % keyword: depression
# % keyword: water table
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_INPUT
# % key: labels
# % description: Depression labels raster (from r.richdem.dephier)
# %end
# %option G_OPT_R_INPUT
# % key: flowdirs
# % description: Flow directions raster (from r.richdem.dephier)
# %end
# %option G_OPT_V_INPUT
# % key: hierarchy
# % description: Depression hierarchy vector map (from r.richdem.dephier)
# %end
# %option G_OPT_R_INPUT
# % key: water_depth
# % description: Input water table depth raster (negative = unsaturated, positive = surface water)
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output water table depth raster after redistribution
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
    from librichdem.vector import depressions_from_grass, update_water_vol

    import numpy as np
    import richdem as rd

    dem = rdarray_from_grass(options["input"])
    wtd = rdarray_from_grass(options["water_depth"])
    deps = depressions_from_grass(options["hierarchy"])

    # FSM requires labels as uint32 and flowdirs as int8; GRASS stores both
    # as DCELL (float64), so we cast after reading.
    _labels_f = rdarray_from_grass(options["labels"])
    _flowdirs_f = rdarray_from_grass(options["flowdirs"])
    labels   = rd.rdarray(np.array(_labels_f,   dtype=np.uint32), no_data=2**32-1,
                          geotransform=_labels_f.geotransform)
    flowdirs = rd.rdarray(np.array(_flowdirs_f, dtype=np.int8),   no_data=-1,
                          geotransform=_flowdirs_f.geotransform)

    rd.fill_spill_merge(dem, labels, flowdirs, deps, wtd)

    rdarray_to_grass(wtd, options["output"], overwrite=gs.overwrite())
    update_water_vol(deps, options["hierarchy"])


if __name__ == "__main__":
    sys.exit(main())
