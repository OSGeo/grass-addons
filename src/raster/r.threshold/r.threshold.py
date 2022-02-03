#!/usr/bin/env python

################################################################################
#
# MODULE:       r.threshold.py
#
# AUTHOR(S):    Margherita Di Leo <dileomargherita@gmail.com>
#
# PURPOSE:      Find optimal threshold for stream extraction
#
# COPYRIGHT:    (c) 2011 by Margherita Di Leo and the GRASS Development Team
#
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
################################################################################

# %module
# % description: Find optimal threshold for stream extraction
# % keyword: raster
# % keyword: hydrology
# % keyword: threshold
# %end

# %option
# % key: acc
# % type: string
# % gisprompt: old,raster,raster
# % key_desc: acc
# % description: Name of accumulation raster map
# % required: yes
# %END

# %flag
# % key: g
# % description: Print the threshold value in shell script style
# %end

from __future__ import print_function
import os
import sys
import math
import numpy as np

import grass.script as grass


def main():
    stats = grass.read_command(
        "r.stats",
        input=options["acc"],
        separator="space",
        nv="*",
        nsteps="1000",
        flags="Anc",
    ).split("\n")[:-1]

    mappatella = np.zeros((len(stats), 3), float)

    # mappatella is a matrix, in the first column the value of upslope area is stored,
    # in the second the number of cells, in the third the distance from origin is calculated

    for i in range(len(stats)):
        mappatella[i, 0], mappatella[i, 1] = map(float, stats[i].split(" "))
        # calculating distance from origin of each point; origin of the plot is in low left point
        mappatella[i, 2] = math.sqrt((mappatella[i, 0] ** 2) + (mappatella[i, 1] ** 2))

    area = mappatella[:, 0]
    num_cells = mappatella[:, 1]
    distance = mappatella[:, 2]

    index = np.where(distance == min(distance))
    th = area[index]

    if th < 0:
        grass.warning("Flow accumulation contains negative values")
        if flags["g"]:
            print("threshold=%d" % th)
    else:
        if flags["g"]:
            print("threshold=%d" % th)
        else:
            grass.message("Suggested threshold is %d" % th)

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
