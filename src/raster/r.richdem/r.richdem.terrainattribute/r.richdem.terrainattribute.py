#!/usr/bin/env python3
# %module
# % description: Calculate terrain attributes using RichDEM
# % keyword: raster
# % keyword: terrain
# % keyword: geomorphology
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Input elevation raster
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# % description: Output terrain attribute raster
# %end
# %option
# % key: attribute
# % type: string
# % options: slope_riserun,slope_percentage,slope_degrees,slope_radians,aspect,curvature,planform_curvature,profile_curvature
# % description: Terrain attribute to calculate
# %end
# %option
# % key: zscale
# % type: double
# % answer: 1.0
# % description: Z-axis scale factor applied before calculation
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
    result = rd.TerrainAttribute(
        dem, attrib=options["attribute"], zscale=float(options["zscale"])
    )
    rdarray_to_grass(result, options["output"], overwrite=gs.overwrite())


if __name__ == "__main__":
    sys.exit(main())
