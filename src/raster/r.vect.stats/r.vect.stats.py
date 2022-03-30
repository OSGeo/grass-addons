#!/usr/bin/env python

############################################################################
#
# MODULE:    r.vect.stats
# AUTHOR(S): Vaclav Petras <wenzeslaus gmail com>
# PURPOSE:
# COPYRIGHT: (C) 2017 by Vaclav Petras and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# %module
# % description: Bins vector points into a raster map.
# % keyword: raster
# % keyword: vector
# % keyword: points
# % keyword: binning
# %end
# %option G_OPT_V_INPUT
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option G_OPT_DB_COLUMN
# % description: Name of attribute column for statistics
# % guisection: Attributes
# %end
# %option
# % key: method
# % type: string
# % required: no
# % multiple: no
# % options: n,min,max,range,sum,mean,stddev,variance,coeff_var,median,percentile,skewness,trimmean
# % description: Statistic to use for raster values
# % descriptions: n;Number of points in cell;min;Minimum value of point values in cell;max;Maximum value of point values in cell;range;Range of point values in cell;sum;Sum of point values in cell;mean;Mean (average) value of point values in cell;stddev;Standard deviation of point values in cell;variance;Variance of point values in cell;coeff_var;Coefficient of variance of point values in cell;median;Median value of point values in cell;percentile;Pth (nth) percentile of point values in cell;skewness;Skewness of point values in cell;trimmean;Trimmed mean of point values in cell
# % answer: mean
# % guisection: Attributes
# %end

import sys

import grass.script as gs
from grass.exceptions import CalledModuleError


def main():
    options, flags = gs.parser()

    vector = options["input"]
    layer = 1
    raster = options["output"]
    method = options["method"]
    z = 3
    sep = "pipe"
    out_args = {}

    if not gs.find_file(vector, element="vector")["fullname"]:
        gs.fatal("Vector map <{0}> not found".format(vector))

    if options["column"]:
        z = 4
        out_args["column"] = options["column"]
        out_args["where"] = "{0} IS NOT NULL".format(options["column"])

        columns = gs.vector_columns(vector)

        if options["column"] not in columns:
            gs.fatal(_("Column <{0}> not found".format(options["column"])))
        if columns[options["column"]]["type"] not in ("INTEGER", "DOUBLE PRECISION"):
            gs.fatal(_("Column <{0}> is not numeric".format(options["column"])))

    out_process = gs.pipe_command(
        "v.out.ascii",
        input=vector,
        layer=layer,
        format="point",
        separator=sep,
        flags="r",
        **out_args,
    )
    in_process = gs.start_command(
        "r.in.xyz",
        input="-",
        output=raster,
        method=method,
        z=z,
        separator=sep,
        stdin=out_process.stdout,
    )
    in_process.communicate()
    out_process.wait()

    return 0


if __name__ == "__main__":
    sys.exit(main())
