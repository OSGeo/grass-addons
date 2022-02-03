#!/usr/bin/env python
#
############################################################################
#
# MODULE:	    i.cva
# AUTHOR(S):	Anna Zanchetta
#
# PURPOSE:	    Performs Change Vector Analysis (CVA) in two dimensions
#
# COPYRIGHT:	(C) 2016 by Anna Zanchetta and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
# References:
# Malila W A, Lafayette W. Change Vector Analysis: An Approach for Detecting
#             Forest Changes with Landsat. LARS Symp. 1980;326-335.
#
#############################################################################

# %Module
# % description: Performs Change Vector Analysis (CVA) in two dimensions.
# % keyword: imagery
# % keyword: transformation
# % keyword: CVA
# % keyword: change vector analysis
# %end
# %option G_OPT_R_INPUT
# % key: xaraster
# % description: Name of the first raster for X axis
# %end
# %option G_OPT_R_INPUT
# % key: xbraster
# % description: Name of the the second raster for X axis
# %end
# %option G_OPT_R_INPUT
# % key: yaraster
# % description: Name of the first raster for Y axis
# %end
# %option G_OPT_R_INPUT
# % key: ybraster
# % description: Name of the second raster for Y axis
# %end
# %option G_OPT_R_BASENAME_OUTPUT
# % label: Name for output basename raster maps (angle and magnitude)
# %end
# %option
# % key: custom_threshold
# % description: Use a custom threshold
# % guisection: Magnitude threshold
# % type: double
# % required: no
# % descriptions: Insert numerical value for the threshold to perform the analysis
# % multiple: no
# %end
# %option
# % key: stat_threshold
# % description: Use a statystical parameter for the threshold (mean + N * standard deviation)
# % guisection: Magnitude threshold
# % type: double
# % required: no
# % descriptions: Insert the integer value for a multiple of standard deviation (to be summed to the mean of the magnitude values )
# % multiple: no
# %end
# %rules
# % exclusive: custom_threshold, stat_threshold
# %end

from __future__ import print_function
import atexit
import sys
import grass.script as grass
from grass import script


TMPRAST = []


def delta_calculation(delta, second_band, first_band):
    """
    Calculates the Delta as difference between the second band and the first band
    """
    equation = "$delta = $second_band - $first_band"
    grass.mapcalc(equation, delta=delta, second_band=second_band, first_band=first_band)


def angle_calculation(anglemap, deltaX, deltaY):
    """
    Calculates the vector angle as the arctg of deltaY/deltaX
    """
    equation = "$anglemap = atan($deltaX,$deltaY)"
    grass.mapcalc(equation, anglemap=anglemap, deltaX=deltaX, deltaY=deltaY)


def magnitude_calculation(magnitudemap, deltaX, deltaY):
    """
    Calculates the vector length (magnitude) as sqrt((deltaX)^2+(deltaY)^2)
    """
    equation = "$magnitudemap = sqrt((($deltaX)^2)+(($deltaY)^2))"
    grass.mapcalc(equation, magnitudemap=magnitudemap, deltaX=deltaX, deltaY=deltaY)


def change_map_calculation(change_map, magnitude_map, threshold, angle_map_class):
    """
    Generates the change map as the values of the classified angle map whose magnitude follows the criterion (values higher than the threshold)
    """
    equation = "$change_map = if($magnitude_map>$threshold,$angle_map_class,null())"
    grass.mapcalc(
        equation,
        change_map=change_map,
        magnitude_map=magnitude_map,
        threshold=threshold,
        angle_map_class=angle_map_class,
    )


def main():
    options, flags = grass.parser()
    xAmap = options["xaraster"]
    xBmap = options["xbraster"]
    yAmap = options["yaraster"]
    yBmap = options["ybraster"]
    output_basename = options["output"]
    custom_threshold = options["custom_threshold"]
    stat_threshold = options["stat_threshold"]
    Xdelta_name = "deltaX"
    Ydelta_name = "deltaY"
    anglemap_name = output_basename + "_angle"
    anglemap_class = anglemap_name + "_class"
    magnitudemap_name = output_basename + "_magnitude"
    changemap_name = output_basename + "_change"

    # Checking that the input maps exist
    if not grass.find_file(name=xAmap, element="cell")["file"]:
        grass.fatal("xaraster map <%s> not found" % xAmap)
    if not grass.find_file(name=xBmap, element="cell")["file"]:
        grass.fatal("xbraster map <%s> not found" % xBmap)
    if not grass.find_file(name=yAmap, element="cell")["file"]:
        grass.fatal("yaraster map <%s> not found" % yAmap)
    if not grass.find_file(name=xBmap, element="cell")["file"]:
        grass.fatal("ybraster map <%s> not found" % yBmap)

    TMPRAST.append(Xdelta_name)
    TMPRAST.append(Ydelta_name)

    # Calculating delta for X and Y bands
    grass.message(_("Calculating DeltaX and DeltaY"))
    delta_calculation(Xdelta_name, xBmap, xAmap)
    delta_calculation(Ydelta_name, yBmap, yAmap)

    # Calculating angle and magnitude maps
    grass.message(_("Writing angle map %s") % anglemap_name)
    angle_calculation(anglemap_name, Xdelta_name, Ydelta_name)

    grass.message(_("Writing magnitude map %s") % magnitudemap_name)
    magnitude_calculation(magnitudemap_name, Xdelta_name, Ydelta_name)

    # Reclassifing angle map to get a map with the four quadrants
    keys = ["1", "2", "3", "4"]
    vals = [0, 90, 180, 270, 360]
    rvals = [
        (int(vals[i - 1]), int(vals[i]), keys[i - 1], vals[i - 1], vals[i])
        for i in range(1, len(vals))
    ]
    rules = "\n".join(["%3d thru %3d = %s   %s-%s" % v for v in rvals])
    script.write_command(
        "r.reclass",
        input=anglemap_name,
        output=anglemap_class,
        rules="-",
        overwrite=True,
        stdin=rules.encode(),
    )

    # Generating the change detection map using the given threshold
    if custom_threshold:
        threshold = custom_threshold
        grass.message(_("Threshold is %s") % threshold)
        grass.message(_("Writing change detection map %s") % changemap_name)
        # Creating the final map of the change, using a custom threshold
        change_map_calculation(
            changemap_name, magnitudemap_name, threshold, anglemap_class
        )
    elif stat_threshold:
        # Getting values of mean and standard dev of magnitude to calculate the change detection criteria (> mean + N*stdev)
        univar = grass.read_command("r.univar", map=magnitudemap_name, flags="g")

        found = 0
        for line in univar.splitlines():
            name, val = line.split("=")
            if name == "mean":
                grass.message(_("Mean of magnitude values is: %s") % val)
                mean = val
                found += 1
            if name == "stddev":
                grass.message(_("Standard deviation of magnitude values is: %s") % val)
                stddev = val
                found += 1
        if found != 2:
            grass.fatal("Couldn't find mean or stddev!")

        adding_value = float(stat_threshold) * float(stddev)
        threshold = float(mean) + float(adding_value)
        grass.message(_("Threshold is %s") % threshold)
        # Creating the final map of the change, using a statistical threshold
        change_map_calculation(
            changemap_name, magnitudemap_name, threshold, anglemap_class
        )
    else:
        grass.message(
            _("No threshold given, only angle and magnitude maps have been created")
        )

    # anglemap_class: set colors
    iva_colors = "1 217 255 0\n2 10 214 10\n3 75 173 255\n4 139 105 20\nnv 255 255 255\ndefault 255 255 255"
    p = grass.feed_command("r.colors", map=anglemap_class, rules="-")
    p.stdin.write(iva_colors.encode())
    p.stdin.close()

    # anglemap_class: set categories
    rules = [
        "1:moisture reduction",
        "2:chlorophyll increase",
        "3:moisture increase",
        "4:bare soil increase",
    ]
    p = grass.feed_command("r.category", map=anglemap_class, rules="-", separator=":")
    p.stdin.write(("\n".join(rules)).encode())
    p.stdin.close()

    return 0


def cleanup():
    # !Delete temporary maps
    TMPRAST.reverse()
    for i in TMPRAST:
        script.run_command("g.remove", flags="f", type="raster", name=i, quiet=True)


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
