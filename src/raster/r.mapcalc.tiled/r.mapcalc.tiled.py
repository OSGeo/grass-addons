#!/usr/bin/env python

############################################################################
#
# MODULE:	r.mapcalc.tiled
# AUTHOR(S):	Moritz Lennert
#
# PURPOSE:	Run r.mapcalc over tiles of the input map
#               to allow parallel processing
# COPYRIGHT:	(C) 2019 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#############################################################################

# %Module
# % description: Runs r.mapcalc in parallel over tiles.
# % keyword: raster
# % keyword: algebra
# % keyword: tiling
# %end
#
# %option
# % key: expression
# % type: string
# % description: Expression to send to r.mapcalc
# % required: yes
# %end
#
# %option G_OPT_R_OUTPUT
# % description: Name of raster output map resulting from expression
# % key: output
# % required : no
# %end
#
# %option
# % key: width
# % type: integer
# % description: Width of tiles (columns)
# % answer: 1000
# % required: yes
# %end
#
# %option
# % key: height
# % type: integer
# % description: Height of tiles (rows)
# % answer: 1000
# % required: yes
# %end
#
# %option
# % key: overlap
# % type: integer
# % description: Overlap of tiles
# % answer: 0
# % required: yes
# %end
#
# %option
# % key: nprocs
# % type: integer
# % description: Number of r.mapcalc processes to run in parallel
# % required: no
# % options: 1-
# %end
#
# %option
# % key: processes
# % type: integer
# % description: Number of r.mapcalc processes to run in parallel, use nprocs option instead
# % label: This option is obsolete and replaced by nprocs
# % required: no
# % options: 1-
# %end
#
# %option
# % key: mapset_prefix
# % type: string
# % description: Mapset prefix
# % required: no
# %end
#
# %rules
# % exclusive: processes,nprocs
# %end

import math
import grass.script as gscript
from grass.pygrass.modules.grid.grid import *


class MyGridModule(GridModule):
    """inherit GridModule, but handle the fact that the output name is in the expression"""

    def patch(self):
        """Patch the final results."""
        bboxes = split_region_tiles(width=self.width, height=self.height)
        loc = Location()
        mset = loc[self.mset.name]
        mset.visible.extend(loc.mapsets())
        output_map = self.out_prefix[:]
        self.out_prefix = ""
        rpatch_map(
            output_map,
            self.mset.name,
            self.msetstr,
            bboxes,
            self.module.flags.overwrite,
            self.start_row,
            self.start_col,
            self.out_prefix,
        )


def main():

    expression = options["expression"]
    width = int(options["width"])
    height = int(options["height"])
    overlap = int(options["overlap"])
    processes = options["nprocs"]
    if not processes:
        processes = options["processes"]
        if processes:
            gscript.warning(_("Option processes is obsolete, use nprocs instead."))
    try:
        processes = int(processes)
    except ValueError:
        processes = 1

    output = None
    if options["output"]:
        output = options["output"]
    mapset_prefix = None
    if options["mapset_prefix"]:
        mapset_prefix = options["mapset_prefix"]

    kwargs = {"expression": expression, "quiet": True}

    if output:
        output_mapname = output
    else:
        output_mapname = expression.split("=")[0].strip()

    grd = MyGridModule(
        "r.mapcalc",
        width=width,
        height=height,
        overlap=overlap,
        processes=processes,
        split=False,
        mapset_prefix=mapset_prefix,
        out_prefix=output_mapname,
        **kwargs,
    )
    grd.run()


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
