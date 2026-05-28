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
# % label: Depression hierarchy vector map (from r.richdem.dephier)
# %end
# %option
# % key: water_depth
# % type: string
# % required: yes
# % label: Depth of water to add (float value or raster map name)
# % description: Uniform depth as a float (e.g. 0.5) or a raster map name. Negative values mean water table is below the surface; positive values mean surface inundation.
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
    _wd = options["water_depth"]
    try:
        _val = float(_wd)
        wtd = rd.rdarray(
            np.full(dem.shape, _val, dtype=np.float64),
            no_data=-9999.0,
            geotransform=dem.geotransform,
        )
    except ValueError:
        wtd = rdarray_from_grass(_wd)
    deps = depressions_from_grass(options["hierarchy"])

    # FSM requires labels as uint32 and flowdirs as int8; GRASS stores both
    # as DCELL (float64), so we cast after reading.
    _labels_f = rdarray_from_grass(options["labels"])
    _flowdirs_f = rdarray_from_grass(options["flowdirs"])
    labels = rd.rdarray(
        np.array(_labels_f, dtype=np.uint32),
        no_data=2**32 - 1,
        geotransform=_labels_f.geotransform,
    )
    flowdirs = rd.rdarray(
        np.array(_flowdirs_f, dtype=np.int8),
        no_data=-1,
        geotransform=_flowdirs_f.geotransform,
    )

    rd.fill_spill_merge(dem, labels, flowdirs, deps, wtd)

    rdarray_to_grass(wtd, options["output"], overwrite=gs.overwrite())
    update_water_vol(deps, options["hierarchy"])


if __name__ == "__main__":
    sys.exit(main())
