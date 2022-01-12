#!/usr/bin/env python

#%module
#% label: Extracts portion of the input map which overlaps with the current region
#% description: Extracts portion of the input raster map which is in the current computational region
#% keyword: raster
#% keyword: extract
#% keyword: clip
#% keyword: crop
#% keyword: trim
#% keyword: extent
#%end
#%option G_OPT_R_INPUT
#%end
#%option G_OPT_R_OUTPUT
#%end
#%flag
#% key: r
#% label: Resample input raster according to the computational region
#% description: By default cell size and alignment of the original raster is preserved
#%end


import sys
import atexit

import grass.script as gs


def main():
    options, flags = gs.parser()

    original = options["input"]
    clipped = options["output"]

    # set region res and grid to match raster to avoid resampling
    if not flags["r"]:
        gs.use_temp_region()
        atexit.register(gs.del_temp_region)
        gs.run_command("g.region", align=original)

    gs.mapcalc("$clipped = $original", clipped=clipped, original=original)


if __name__ == "__main__":
    sys.exit(main())
