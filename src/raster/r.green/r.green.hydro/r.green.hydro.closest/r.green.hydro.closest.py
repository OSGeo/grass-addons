#!/usr/bin/env python
# -- coding: utf-8 --
#
############################################################################
#
# MODULE:      r.green.hydro.potential
# AUTHOR(S):   Pietro Zambelli
# PURPOSE:     Calculate the hydropower energy potential for each basin
# COPYRIGHT:   (C) 2014 by the GRASS Development Team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################
#

# %module
# % description: Move points to the closest vector map
# % keyword: vector
# % keyword: hydropower
# % keyword: renewable energy
# %end
# %option G_OPT_V_INPUT
# % key: points
# % required: yes
# %end
# %option G_OPT_V_INPUT
# % key: lines
# % required: yes
# %end
# %option G_OPT_V_OUTPUT
# % key: output
# % required: yes
# %end
# %option
# % key: max_dist
# % type: double
# % description: Maximum distance from points to river
# % required: yes
# % answer: 10
# %end
from __future__ import print_function

# import system libraries
import os
import sys

from grass.pygrass.messages import get_msgr
from grass.pygrass.vector import VectorTopo
from grass.script import core as gcore

if "GISBASE" not in os.environ:
    print("You must be in GRASS GIS to run this program.")
    sys.exit(1)


def get_new_points(points, lines, output, maxdist=50):
    skipped = []
    ovwr = gcore.overwrite()
    msgr = get_msgr()
    points, pmset = points.split("@") if "@" in points else (points, "")
    lines, lmset = lines.split("@") if "@" in lines else (lines, "")
    with VectorTopo(points, mapset=pmset, mode="r") as pts:
        cols = list(pts.table.columns.items()) if pts.table else None
        with VectorTopo(lines, mapset=lmset, mode="r") as lns:
            with VectorTopo(output, mode="w", tab_cols=cols, overwrite=ovwr) as out:
                for pnt in pts:
                    line = lns.find["by_point"].geo(pnt, maxdist=maxdist)
                    if line is None:
                        msg = (
                            "Not found any line in the radius of %.2f "
                            "for the point with cat: %d. The point "
                            "will be skipped!"
                        )
                        msgr.warning(msg % (maxdist, pnt.cat))
                        skipped.append(pnt.cat)
                        continue
                    # find the new point
                    newpnt, dist, _, _ = line.distance(pnt)
                    # get the attributes
                    attrs = None if pnt.attrs is None else list(pnt.attrs.values())[1:]
                    # write the new point in the new vector map
                    out.write(newpnt, attrs)
                # save the changes on the output table
                out.table.conn.commit()


def main(opts, flgs):
    get_new_points(
        opts["points"], opts["lines"], opts["output"], float(opts["max_dist"])
    )


if __name__ == "__main__":
    options, flags = gcore.parser()
    sys.exit(main(options, flags))
