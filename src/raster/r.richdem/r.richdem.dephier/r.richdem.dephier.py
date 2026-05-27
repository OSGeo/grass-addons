#!/usr/bin/env python3
# %module
# % description: Compute the depression hierarchy of a DEM using RichDEM
# % keyword: raster
# % keyword: vector
# % keyword: hydrology
# % keyword: depression hierarchy
# % keyword: flow direction
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output_labels
# % description: Output depression labels raster (leaf depression index per cell)
# %end
# %option G_OPT_R_OUTPUT
# % key: output_flowdirs
# % description: Output flow directions raster
# %end
# %option G_OPT_V_OUTPUT
# % key: output_hierarchy
# % description: Output depression hierarchy vector map
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
    from librichdem.vector import depressions_to_grass

    import richdem as rd

    dem = rdarray_from_grass(options["input"])
    labels = rd.get_new_depression_hierarchy_labels(dem.shape, geotransform=dem.geotransform)
    deps, flowdirs = rd.get_depression_hierarchy(dem, labels)

    rdarray_to_grass(labels, options["output_labels"], overwrite=gs.overwrite())
    rdarray_to_grass(flowdirs, options["output_flowdirs"], overwrite=gs.overwrite())
    depressions_to_grass(deps, labels, flowdirs, options["output_hierarchy"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
