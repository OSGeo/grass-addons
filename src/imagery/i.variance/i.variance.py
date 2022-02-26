#!/usr/bin/env python

############################################################################
#
# MODULE:        i.variance
# AUTHOR(S):        Moritz Lennert
#
# PURPOSE:        Calculate variation of variance by variation of resolution
# COPYRIGHT:        (C) 1997-2016 by the GRASS Development Team
#
#                This program is free software under the GNU General Public
#                License (>=v2). Read the file COPYING that comes with GRASS
#                for details.
#
#############################################################################
# Curtis E. Woodcock, Alan H. Strahler, The factor of scale in remote sensing,
# Remote Sensing of Environment, Volume 21, Issue 3, April 1987, Pages 311-332,
# ISSN 0034-4257, http://dx.doi.org/10.1016/0034-4257(87)90015-0.
#
#############################################################################

# %Module
# % description: Analyses variation of variance with variation of resolution
# % keyword: imagery
# % keyword: variance
# % keyword: resolution
# %end
#
# %option G_OPT_R_INPUT
# % description: Raster band  on which to perform analysis of variation of variance
# %end
#
# %option G_OPT_F_OUTPUT
# % key: csv_output
# % label: Name for output file
# % required: no
# %end
#
# %option G_OPT_F_OUTPUT
# % key: plot_output
# % label: Name for graphic output file for plot (extension decides format, - for screen)
# % required: no
# %end
#
# %option
# % key: min_cells
# % type: integer
# % description: Minimum number of cells at which to stop
# % required: no
# % multiple: no
# %end
#
# %option
# % key: max_size
# % type: double
# % description: Maximum pixel size (= minimum resolution) to analyse
# % required: no
# % multiple: no
# %end
#
# %option
# % key: step
# % type: double
# % description: Step of resolution variation
# % required: yes
# % answer: 1
# % multiple: no
# %end
#
# %rules
# % required: min_cells,max_size
# %end

import sys
import os
import atexit
from math import sqrt
import grass.script as gscript


def cleanup():
    if gscript.find_file(temp_resamp_map, element="raster")["name"]:
        gscript.run_command(
            "g.remove", flags="f", type="raster", name=temp_resamp_map, quiet=True
        )
    if gscript.find_file(temp_variance_map, element="raster")["name"]:
        gscript.run_command(
            "g.remove", flags="f", type="raster", name=temp_variance_map, quiet=True
        )


def FindMaxima(numbers):
    maxima = []
    differences = []
    length = len(numbers)
    if length >= 2:
        if numbers[0] > numbers[1]:
            maxima.append(0)
            differences.append(numbers[0] - numbers[1])

        if length > 3:
            for i in range(1, length - 1):
                if numbers[i] > numbers[i - 1] and numbers[i] > numbers[i + 1]:
                    maxima.append(i)
                    differences.append(
                        min(numbers[i] - numbers[i - 1], numbers[i] - numbers[i + 1])
                    )

        if numbers[length - 1] > numbers[length - 2]:
            maxima.append(length - 1)
            differences.append(numbers[length - 1] - numbers[length - 2])

    return maxima, differences


def main():
    import matplotlib  # required by windows

    matplotlib.use("wxAGG")  # required by windows
    import matplotlib.pyplot as plt

    input = options["input"]
    output = None
    if options["csv_output"]:
        output = options["csv_output"]
    plot_output = None
    if options["plot_output"]:
        plot_output = options["plot_output"]
    min_cells = False
    if options["min_cells"]:
        min_cells = int(options["min_cells"])
    target_res = None
    if options["max_size"]:
        target_res = float(options["max_size"])
    step = float(options["step"])

    global temp_resamp_map, temp_variance_map
    temp_resamp_map = "temp_resamp_map_%d" % os.getpid()
    temp_variance_map = "temp_variance_map_%d" % os.getpid()
    resolutions = []
    variances = []

    region = gscript.parse_command("g.region", flags="g")
    cells = int(region["cells"])
    res = (float(region["nsres"]) + float(region["ewres"])) / 2
    north = float(region["n"])
    south = float(region["s"])
    west = float(region["w"])
    east = float(region["e"])

    if res % 1 == 0 and step % 1 == 0:
        template_string = "%d,%f\n"
    else:
        template_string = "%f,%f\n"

    if min_cells:
        target_res_cells = int(sqrt(((east - west) * (north - south)) / min_cells))
        if target_res > target_res_cells:
            target_res = target_res_cells
            gscript.message(
                _(
                    "Max resolution leads to less cells than defined by 'min_cells' (%d)."
                    % min_cells
                )
            )
            gscript.message(_("Max resolution reduced to %d" % target_res))

    nb_iterations = target_res - res / step
    if nb_iterations < 3:
        message = _("Less than 3 iterations. Cannot determine maxima.\n")
        message += _("Please increase max_size or reduce min_cells.")
        gscript.fatal(_(message))

    gscript.use_temp_region()

    gscript.message(_("Calculating variance at different resolutions"))
    while res <= target_res:
        gscript.percent(res, target_res, step)
        gscript.run_command(
            "r.resamp.stats",
            input=input,
            output=temp_resamp_map,
            method="average",
            quiet=True,
            overwrite=True,
        )
        gscript.run_command(
            "r.neighbors",
            input=temp_resamp_map,
            method="variance",
            output=temp_variance_map,
            quiet=True,
            overwrite=True,
        )
        varianceinfo = gscript.parse_command(
            "r.univar", map_=temp_variance_map, flags="g", quiet=True
        )
        resolutions.append(res)
        variances.append(float(varianceinfo["mean"]))
        res += step
        region = gscript.parse_command(
            "g.region", res=res, n=north, s=south, w=west, e=east, flags="ag"
        )
        cells = int(region["cells"])

    indices, differences = FindMaxima(variances)
    max_resolutions = [resolutions[x] for x in indices]
    gscript.message(_("resolution,min_diff"))
    for i in range(len(max_resolutions)):
        print("%g,%g" % (max_resolutions[i], differences[i]))

    if output:
        header = "resolution,variance\n"
        of = open(output, "w")
        of.write(header)
        for i in range(len(resolutions)):
            output_string = template_string % (resolutions[i], variances[i])
            of.write(output_string)
        of.close()

    if plot_output:
        plt.plot(resolutions, variances)
        plt.xlabel("Resolution")
        plt.ylabel("Variance")
        plt.grid(True)
        if plot_output == "-":
            plt.show()
        else:
            plt.savefig(plot_output)


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
