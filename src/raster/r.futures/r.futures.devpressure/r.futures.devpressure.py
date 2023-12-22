#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
##############################################################################
#
# MODULE:       r.futures.devpressure
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      FUTURES development pressure computation
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################

#%module
#% description: Module for computing development pressure
#% keyword: raster
#% keyword: filter
#% keyword: statistics
#%end
#%option G_OPT_R_INPUT
#% description: Name of input binary raster map representing development
#%end
#%option G_OPT_R_OUTPUT
#% description: Name of the output development pressure raster
#%end
#%option
#% key: method
#% type: string
#% description: Method for computing development pressure
#% required: yes
#% answer: gravity
#% options: occurrence,gravity,kernel
#% descriptions: occurrence;number of developed cells in window;gravity;scaling_factor / pow(distance, gamma);kernel;scaling_factor * exp (-2*distance / gamma)
#%end
#%option
#% key: size
#% type: integer
#% description: Half of neighborhood size
#% required: yes
#% answer: 8
#%end
#%option
#% key: gamma
#% type: double
#% description: Coefficient controlling the influence of distance, needed for method gravity and kernel
#% required: no
#% answer: 1.5
#%end
#%option
#% key: scaling_factor
#% type: double
#% description: Scaling factor needed for method gravity and kernel
#% required: no
#% answer: 1
#%end
#%flag
#% key: n
#% description: Do not propagate nulls
#%end


import os
import sys
import atexit
import numpy as np
from math import sqrt

# from grass.exceptions import CalledModuleError
import grass.script.core as gcore
import grass.script.utils as gutils
import grass.script.raster as grast

TMPFILE = None
TMP = []


def cleanup():
    if TMP:
        gcore.run_command("g.remove", flags="f", type=["raster"], name=TMP)
    gutils.try_remove(TMPFILE)


def main():
    size = int(options["size"])
    gamma = scale = None
    if options["gamma"]:
        gamma = float(options["gamma"])
    if options["scaling_factor"]:
        scale = float(options["scaling_factor"])
    input_dev = options["input"]
    output = options["output"]
    method = options["method"]

    if method in ("gravity", "kernel") and (gamma is None or scale is None):
        gcore.fatal(
            _("Methods gravity and kernel require options scaling_factor and gamma")
        )

    temp_map = "tmp_futures_devPressure_" + str(os.getpid()) + "_copy"
    temp_map_out = "tmp_futures_devPressure_" + str(os.getpid()) + "_out"
    temp_map_nulls = "tmp_futures_devPressure_" + str(os.getpid()) + "_nulls"
    global TMP, TMPFILE
    if flags["n"]:
        gcore.message(_("Preparing data..."))
        region = gcore.region()
        gcore.use_temp_region()
        gcore.run_command(
            "g.region",
            n=region["n"] + size * region["nsres"],
            s=region["s"] - size * region["nsres"],
            e=region["e"] + size * region["ewres"],
            w=region["w"] - size * region["ewres"],
        )
        TMP.append(temp_map)
        TMP.append(temp_map_nulls)
        TMP.append(temp_map_out)
        exp = "{temp_map_nulls} = if(isnull({inp}), 1, null())".format(
            temp_map_nulls=temp_map_nulls, inp=input_dev
        )
        grast.mapcalc(exp=exp)
        grast.mapcalc(
            exp="{temp} = if(isnull({inp}), 0, {inp})".format(
                temp=temp_map, inp=input_dev
            )
        )
        rmfilter_inp = temp_map
        rmfilter_out = temp_map_out
    else:
        rmfilter_inp = input_dev
        rmfilter_out = output

    matrix = distance_matrix(size)
    if method == "occurrence":
        matrix[matrix > 0] = 1
    elif method == "gravity":
        with np.errstate(divide="ignore"):
            denom = np.power(matrix, gamma)
            matrix = scale / denom
            matrix[denom == 0] = 0
    else:
        matrix_ = scale * np.exp(-2 * matrix / gamma)
        matrix = np.where(matrix > 0, matrix_, 0)

    path = gcore.tempfile()
    global TMPFILE
    TMPFILE = path

    with open(path, "w") as f:
        f.write(write_filter(matrix))
    gcore.message(_("Running development pressure filter..."))
    gcore.run_command("r.mfilter", input=rmfilter_inp, output=rmfilter_out, filter=path)

    if flags["n"]:
        gcore.run_command(
            "g.region",
            n=region["n"],
            s=region["s"],
            e=region["e"],
            w=region["w"],
        )
        grast.mapcalc(
            exp="{out} = if(isnull({temp_null}), {rmfilter_out}, null())".format(
                temp_null=temp_map_nulls, rmfilter_out=rmfilter_out, out=output
            )
        )
        gcore.del_temp_region()

    grast.raster_history(output)


def distance_matrix(size):
    matrix_size = 2 * size + 1
    matrix = np.zeros((matrix_size, matrix_size))
    center = size
    for i in range(matrix_size):
        for j in range(matrix_size):
            dist = sqrt((i - center) * (i - center) + (j - center) * (j - center))
            if dist <= size:
                matrix[i, j] = dist
    return matrix


def write_filter(matrix):
    filter_text = ["TITLE development pressure"]
    filter_text.append("MATRIX %s" % matrix.shape[0])
    for i in range(matrix.shape[0]):
        line = ""
        for j in range(matrix.shape[0]):
            line += str(matrix[i, j])
            line += " "
        filter_text.append(line)
    filter_text.append("DIVISOR 1")
    filter_text.append("TYPE P")

    return "\n".join(filter_text)


if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
