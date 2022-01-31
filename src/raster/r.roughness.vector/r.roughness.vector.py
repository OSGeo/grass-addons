#!/usr/bin/env python
# -*- coding:utf-8 -*-
#
#
############################################################################
#
# MODULE:	r.roughness.vector.py
# AUTHOR(S):	Carlos H. Grohmann <carlos dot grohmann at gmail dot com >
#               Helmut Kudrnovsky <alectoria at gmx dot at>
#
# PURPOSE:	Calculates surface roughness from DEMs.
#       Python version of r.roughness.vector.sh
#
# 		In this script surface roughness is taken as the dispersion
# 		of vectors normal to surface areas (pixels). Normal vectors
# 		are defined by slope and aspect.
# 		Reference:
# 		Hobson, R.D., 1972. Surface roughness in topography:
# 		quantitative approach. In: Chorley, R.J. (ed) Spatial
# 		analysis in geomorphology. Methuer, London, p.225-245.
#
# 		This script will create several temporary maps, for the
# 		directional cosines in each direction (x,y,z), for the sum
# 		of these cosines and vector strength.
#
# 		If the user does not specify the output map name, it will be
# 		set to INPUT_MAP_roughness_vector_NxN
# 		where N is the window size.
#
# COPYRIGHT:	(C) 2014 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#############################################################################
#
# %Module
# % description: Calculates surface roughness in a moving-window, as the orientation of vectors normal to surface planes.
# % keyword: raster
# % keyword: terrain
# % keyword: aspect
# % keyword: slope
# % keyword: roughness
# %end
# %option G_OPT_R_ELEV
# % key: elevation
# % description: Name of elevation raster map
# % required: yes
# %end
# %option
# % key: slope
# % type: string
# % gisprompt: old,cell,raster
# % description: Input slope map
# % required : yes
# %end
# %option
# % key: aspect
# % type: string
# % gisprompt: old,cell,raster
# % description: Input aspect map
# % required : yes
# %end
# %option
# % key: window
# % type: integer
# % description: Moving-window size (uses r.neighbors)
# % required : no
# % answer : 3
# %end
# %option
# % key: strength
# % type: string
# % gisprompt: old,cell,raster
# % description: Output "vector strength" map
# % required : no
# %end
# %option
# % key: fisher
# % type: string
# % gisprompt: old,cell,raster
# % description: Output "Fisher's K parameter" map
# % required : no
# %end
# %option
# % key: compass
# % type: string
# % gisprompt: old,cell,raster
# % description: Input compass aspect map (optional)
# % required : no
# %end
# %option
# % key: colatitude
# % type: string
# % gisprompt: old,cell,raster
# % description: Input colatitude map (optional)
# % required : no
# %end
# %option
# % key: xcos
# % type: string
# % gisprompt: old,cell,raster
# % description: Input x directional cosine map (optional)
# % required : no
# %end
# %option
# % key: ycos
# % type: string
# % gisprompt: old,cell,raster
# % description: Input y directional cosine map (optional)
# % required : no
# %end
# %option
# % key: zcos
# % type: string
# % gisprompt: old,cell,raster
# % description: Input z directional cosine map (optional)
# % required : no
# %end
#

import sys
import atexit
import grass.script as grass

# cleaning up temp files
def cleanup():
    rasts = [
        "aspect_compass",
        "colat_angle",
        "cosine_x",
        "cosine_y",
        "cosine_z",
        "sum_Xcosine",
        "sum_Ycosine",
        "sum_Zcosine",
    ]
    grass.run_command("g.remove", flags="bf", type="raster", name=rasts, quiet=True)


def main():

    # set options
    elevmap = options["elevation"]  # input
    slope = options["slope"]  # input
    aspect = options["aspect"]  # input
    window = options["window"]  # input
    strength = options["strength"]  # output
    fisher = options["fisher"]  # output
    compass = options["compass"]  # temporary
    colatitude = options["colatitude"]  # temporary
    xcos = options["xcos"]  # temporary
    ycos = options["ycos"]  # temporary
    zcos = options["zcos"]  # temporary

    # check if input files exist
    grass.message("----")
    grass.message("Check if input files exist ...")

    find_elev = grass.find_file(elevmap, element="cell")
    if find_elev["name"] == "":
        print("Map %s not found! Aborting." % elevmap)
        sys.exit()

    find_slope = grass.find_file(slope, element="cell")
    if find_slope["name"] == "":
        print("Map %s not found! Aborting." % slope)
        sys.exit()

    find_aspect = grass.find_file(aspect, element="cell")
    if find_aspect["name"] == "":
        print("Map %s not found! Aborting." % aspect)
        sys.exit()

    #########################################################################################################

    # ACERTAR O NOME DOS ARQUIVOS - TIRAR TUDO DESDE O @!!!!

    #########################################################################################################

    # give default names to outputs, in case the user doesn't provide them
    grass.message("----")
    grass.message("Define default output names when not defined by user ...")

    if strength == "":
        strength = "%s_vector_strength_%sx%s" % (find_elev["name"], window, window)

    if fisher == "":
        fisher = "%s_fisher_1K_%sx%s" % (find_elev["name"], window, window)

    #####################
    # calculate compass-oriented aspect and colatitude
    # (temp rasters)

    # correct aspect angles from cartesian (GRASS default) to compass angles
    #   if(A==0,0,if(A < 90, 90-A, 360+90-A))

    grass.message("----")
    grass.message("Calculate compass aspect values ...")

    if compass == "":
        aspect_compass = "aspect_compass"
        #        aspect_compass = grass.tempfile()
        grass.mapcalc(
            "${out} = if(${rast1}==0,0,if(${rast1} < 90, 90-${rast1}, 360+90-${rast1}))",
            out=aspect_compass,
            rast1=aspect,
        )
    else:
        grass.message("Using previous calculated compass aspect values (longitude)")
        aspect_compass = compass

    # calculates colatitude (90-slope)

    grass.message("----")
    grass.message("Calculate colatitude ...")

    if colatitude == "":
        colat_angle = "colat_angle"
        #        colat_angle = grass.tempfile()
        grass.mapcalc("${out} = 90 - ${rast1}", out=colat_angle, rast1=slope)
    else:
        grass.message("Using previous calculated colatitude values")
        colat_angle = colatitude

    #####################
    # calculate direction cosines
    # direction cosines relative to axis oriented north, east and up
    # direction cosine calculation according to McKean & Roering (2004), Geomorphology, 57:331-351.

    grass.message("----")
    grass.message("Calculate direction cosines ...")

    # X cosine
    if xcos == "":
        cosine_x = "cosine_x"
        #        cosine_x = grass.tempfile()
        grass.mapcalc(
            "${out} = sin(${rast1}) * cos(${rast2})",
            out="cosine_x",
            rast1=aspect_compass,
            rast2=colat_angle,
        )
    else:
        grass.message("Using previous calculated X direction cosine value")
        cosine_x = xcos

    # Y cosine
    if ycos == "":
        cosine_y = "cosine_y"
        #        cosine_y = grass.tempfile()
        grass.mapcalc(
            "${out} = sin(${rast1}) * sin(${rast2})",
            out="cosine_y",
            rast1=aspect_compass,
            rast2=colat_angle,
        )
    else:
        grass.message("Using previous calculated Y direction cosine values")
        cosine_y = ycos

    # Z cosine
    if zcos == "":
        cosine_z = "cosine_z"
        #        cosine_z = grass.tempfile()
        grass.mapcalc("${out} = cos(${rast1})", out="cosine_z", rast1=aspect_compass)
    else:
        grass.message("Using previous calculated Y direction cosine values")
        cosine_z = zcos

    # calculate SUM of direction cosines

    grass.message("----")
    grass.message("Calculate sum of direction cosines ...")

    grass.message("Calculating sum of X direction cosines ...")
    #    sum_Xcosine = grass.tempfile()
    grass.run_command(
        "r.neighbors",
        input=cosine_x,
        output="sum_Xcosine",
        method="sum",
        size=window,
        overwrite=True,
    )

    grass.message("Calculating sum of Y direction cosines ...")
    #    sum_Ycosine = grass.tempfile()
    grass.run_command(
        "r.neighbors",
        input=cosine_y,
        output="sum_Ycosine",
        method="sum",
        size=window,
        overwrite=True,
    )

    grass.message("Calculating sum of Z direction cosines ...")
    #    sum_Zcosine = grass.tempfile()
    grass.run_command(
        "r.neighbors",
        input=cosine_z,
        output="sum_Zcosine",
        method="sum",
        size=window,
        overwrite=True,
    )

    #####################
    # calculate vector strength

    grass.message("----")
    grass.message("Calculate vector strength ...")

    #    print strength
    grass.mapcalc(
        "${out} = sqrt(exp(${rast1},2) + exp(${rast2},2) + exp(${rast3},2))",
        out=strength,
        rast1="sum_Xcosine",
        rast2="sum_Ycosine",
        rast3="sum_Zcosine",
    )

    # calculate Inverted Fisher's K parameter
    # k=1/((N-1)/(N-R))

    grass.message("----")
    grass.message("Calculate inverted Fisher's K parameter ...")

    w = int(window)
    grass.mapcalc(
        "${out} = ($w * $w - ${rast1}) / ($w * $w - 1)",
        out=fisher,
        rast1=strength,
        w=int(window),
    )

    #    calculations done

    grass.message("----")
    grass.message("Result maps:")
    grass.message(strength)
    grass.message(fisher)
    grass.message("Calculations done.")
    grass.message("----")


# this "if" condition instructs execution of code contained in this script, *only* if the script is being executed directly
if (
    __name__ == "__main__"
):  # this allows the script to be used as a module in other scripts or as a standalone script
    options, flags = grass.parser()  #
    atexit.register(cleanup)
    sys.exit(main())  #
