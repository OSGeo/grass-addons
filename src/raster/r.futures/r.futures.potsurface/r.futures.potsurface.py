#!/usr/bin/env python3
#
##############################################################################
#
# MODULE:       r.futures.potsurface
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      FUTURES Potential surface for visualization
#
# COPYRIGHT:    (C) 2016-2020 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

# %module
# % description: Module for computing development potential surface from CSV file created by r.futures.potential and predictors
# % keyword: raster
# % keyword: statistics
# %end
# %option G_OPT_F_INPUT
# % description: CSV file with coefficients
# % required: yes
# %end
# %option G_OPT_R_INPUT
# % key: subregions
# % description: Raster map of subregions
# % required: yes
# %end
# %option G_OPT_R_OUTPUT
# % description: Output probability raster
# %end
# %option G_OPT_F_SEP
# % required: no
# % label: Separator used in input CSV file
# % answer: comma
# %end


import sys
import grass.script as gscript


def main():
    csv = options["input"]
    output = options["output"]
    subregions = options["subregions"]
    sep = gscript.separator(options["separator"])

    data = {}
    with open(csv, "r") as f:
        lines = f.read().splitlines()
    header = lines[0].strip().split(sep)
    maps = header[2:]
    for line in lines[1:]:
        if not line:
            continue
        items = line.strip().split(sep)
        data[items[0]] = items[1:]

    expr = "eval(tmp = "
    for i in data.keys():
        expr += "if ({sub} == {ind}, {interc}".format(
            sub=subregions, ind=i, interc=data[i][0]
        )
        for j, m in enumerate(maps):
            expr += " + {coef} * {map}".format(coef=data[i][1 + j], map=m)
        expr += ", "
    expr += "null()"
    expr += ")" * len(data.keys())
    expr += ")"  # for eval
    expr += "\n {new} = 1.0 / (1.0 + exp(-tmp))".format(new=output)
    gscript.debug(expr, 1)
    gscript.mapcalc(expr)


if __name__ == "__main__":
    options, flags = gscript.parser()
    sys.exit(main())
