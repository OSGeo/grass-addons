#!/usr/bin/env python

############################################################################
#
# MODULE:        v.area.weigh
# AUTHOR(S):        Markus Metz
# PURPOSE:        Rasterize vector areas using cell weights
# COPYRIGHT:        (C) 2013 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################

# %module
# % description: Rasterize vector areas using weights
# % keyword: vector
# % keyword: interpolation
# % keyword: raster
# %end
# %option G_OPT_V_INPUT
# % key: vector
# %end
# %option G_OPT_V_FIELD
# %end
# %option G_OPT_DB_COLUMN
# % description: Name of attribute column to use as area values (must be numeric)
# %end
# %option G_OPT_R_INPUT
# % key: weight
# % description: Name of input raster with weights per cell
# %end
# %option G_OPT_R_OUTPUT
# %end

import sys
import os
import atexit
import grass.script as grass
from grass.exceptions import CalledModuleError


def cleanup():
    if rastertmp1:
        grass.run_command(
            "g.remove", flags="f", type="raster", name=rastertmp1, quiet=True
        )
    if rastertmp2:
        grass.run_command(
            "g.remove", flags="f", type="raster", name=rastertmp2, quiet=True
        )
    if rastertmp3:
        grass.run_command(
            "g.remove", flags="f", type="raster", name=rastertmp3, quiet=True
        )


def main():
    global tmp, tmpname, rastertmp1, rastertmp2, rastertmp3
    rastertmp1 = False
    rastertmp2 = False
    rastertmp3 = False

    #### setup temporary files
    tmp = grass.tempfile()
    # we need a random name
    tmpname = grass.basename(tmp)

    vector = options["vector"]
    layer = options["layer"]
    column = options["column"]
    weight = options["weight"]
    output = options["output"]

    # vector exists?
    result = grass.find_file(vector, element="vector")
    if len(result["name"]) == 0:
        grass.fatal(_("Input vector <%s> not found") % vector)

    # raster exists?
    result = grass.find_file(weight, element="cell")
    if len(result["name"]) == 0:
        grass.fatal(_("Input weight raster <%s> not found") % weight)

    # column exists ?
    if column not in grass.vector_columns(vector, layer).keys():
        grass.fatal(
            _("Column does not exist for vector <%s>, layer %s") % (vector, layer)
        )

    # is column numeric?
    coltype = grass.vector_columns(vector, layer)[column]["type"]

    if coltype not in ("INTEGER", "DOUBLE PRECISION"):
        grass.fatal(_("Column must be numeric"))

    # rasterize with cats (will be base layer)
    # strip off mapset for tmp output
    vector_basename = vector.split("@")[0]
    rastertmp1 = "%s_%s_1" % (vector_basename, tmpname)
    try:
        grass.run_command(
            "v.to.rast", input=vector, output=rastertmp1, use="cat", quiet=True
        )
    except CalledModuleError:
        grass.fatal(_("An error occurred while converting vector to raster"))

    # rasterize with column
    rastertmp2 = "%s_%s_2" % (vector_basename, tmpname)
    try:
        grass.run_command(
            "v.to.rast",
            input=vector,
            output=rastertmp2,
            use="attr",
            layer=layer,
            attrcolumn=column,
            quiet=True,
        )
    except CalledModuleError:
        grass.fatal(_("An error occurred while converting vector to raster"))

    # zonal statistics
    rastertmp3 = "%s_%s_3" % (vector_basename, tmpname)
    try:
        grass.run_command(
            "r.stats.zonal",
            base=rastertmp1,
            cover=weight,
            method="sum",
            output=rastertmp3,
            quiet=True,
        )
    except CalledModuleError:
        grass.fatal(_("An error occurred while calculating zonal statistics"))

    # weighted interpolation
    exp = "$output = if($sumweight == 0, if(isnull($area_val), null(), 0), double($area_val) * $weight / $sumweight)"

    grass.mapcalc(
        exp, output=output, sumweight=rastertmp3, area_val=rastertmp2, weight=weight
    )

    sys.exit(0)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
