#!/usr/bin/env python
# coding=utf-8
#
############################################################################
#
# MODULE:       i.cloud.shadow
# AUTHOR(S):    Stefan Blumentrath, Roberta Fagandini
# PURPOSE:      Detects cloud shadows among dark pixels in imagery data
#
# COPYRIGHT:    (C) 2020 by Stefan Blumentrath, Roberta Fagandini, and the GRASS Development Team
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
#
#############################################################################

#%Module
#% description:.
#% keyword: imagery
#% keyword: satellite
#% keyword: cloud
#% keyword: shadow
#% keyword: cloud shadow
#% keyword: reflectance
#%End

#%option G_OPT_R_INPUT
#% key: clouds
#% description: Input raster map with cloud pixels
#%end

#%option G_OPT_R_INPUT
#% key: dark_pixels
#% description: Input raster map with dark pixels (probable shadow)
#%end

#%option
#% key: sun_azimuth
#% description: Sun azimuth
#% type: double
#% required : yes
#%end

#%option
#% key: sun_zenith
#% description: Sun zenith
#% type: double
#% required : yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Name of the output raster map with cloud, cloud shadow and other dark pixels
#%end

#%option
#% key: height_minimum
#% type: integer
#% description: Minimum cloud height
#% required : yes
#% answer: 1000
#% guisection: Settings
#%end

#%option
#% key: height_maximum
#% type: integer
#% description: Maximum cloud height
#% required : yes
#% answer: 4000
#% guisection: Settings
#%end

#%option
#% key: height_steps
#% type: integer
#% description: Steps for assessing cloud height
#% required : yes
#% answer: 100
#% guisection: Settings
#%end

#%option
#% key: cloud_size_threshold
#% type: integer
#% description: Threshold for cleaning small areas from cloud mask (<0 = no cleaning)
#% required : no
#% answer: -1
#% guisection: Settings
#%end

#%option
#% key: shadow_size_threshold
#% type: integer
#% description: Threshold for cleaning small areas from shadow mask in hectares (<0 = no cleaning)
#% required : no
#% answer: -1
#% guisection: Settings
#%end


import math
import os
import sys
import shutil
import subprocess
import re
import glob
import time
import atexit

import numpy
import grass.script as gscript


def get_overlap(clouds, dark_pixels, old_region, new_region):
    # move map
    gscript.run_command(
        "r.region",
        map=clouds,
        n=new_region["n"],
        s=new_region["s"],
        e=new_region["e"],
        w=new_region["w"],
    )
    # measure overlap
    overlap = int(
        gscript.read_command(
            "r.stats",
            flags="c",
            input="{}{}".format(clouds, dark_pixels),
            separator=",",
        )
        .strip()
        .split(",")[2]
    )
    # move map back
    gscript.run_command(
        "r.region",
        map=clouds,
        n=old_region["n"],
        s=old_region["s"],
        e=old_region["e"],
        w=old_region["w"],
    )

    return overlap


def main():

    # Temporary map names
    global tempname
    tempname = gscript.tempname(12)

    # Input file
    output = options["output"]
    clouds = options["clouds"]
    dark_pixels = options["dark_pixels"]
    height_minimum = options["height_minimum"]
    height_maximum = options["height_maximum"]
    height_steps = options["height_steps"]
    sun_zenith = float(options["sun_zenith"])
    sun_azimuth = float(options["sun_azimuth"])
    cloud_size_threshold = options["cloud_size_threshold"]
    shadow_size_threshold = options["shadow_size_threshold"]

    if cloud_size_threshold > 0:
        gscript.run_command(
            "r.reclass.area",
            input=clouds,
            output="{}_clouds".format(tempname),
            mode="greater",
            value=cloud_size_threshold,
        )
        clouds = "{}_clouds".format(tempname)

    if shadow_size_threshold > 0:
        gscript.run_command(
            "r.reclass.area",
            input=dark_pixels,
            output="{}_dark_pixels".format(tempname),
            mode="greater",
            value=shadow_size_threshold,
        )
        dark_pixels = "{}_dark_pixels".format(tempname)

    # Start computing the east and north shift for clouds and the
    # overlapping area between clouds and dark_pixels at user given steps
    gscript.verbose(
        _(
            "--- Start computing the east and north clouds shift at steps of {}m of clouds height---".format(
                height_steps
            )
        )
    )
    height = height_minimum
    gscript.run_command("g.copy", raster="{},{}".format(clouds, tempname))
    map_region = gscript.raster.raster_info(tempname)
    heights = []
    shifts = []
    overlap_areas = []
    while height <= height_maximum:
        z_deg_to_rad = math.radians(sun_zenith)
        tan_Z = math.tan(z_deg_to_rad)
        a_deg_to_rad = math.radians(sun_azimuth)
        cos_A = math.cos(a_deg_to_rad)
        sin_A = math.sin(a_deg_to_rad)

        E_shift = -height * tan_Z * sin_A
        N_shift = -height * tan_Z * cos_A

        new_region = {
            "n": float(map_region["n"]) + N_shift,
            "s": float(map_region["s"]) + N_shift,
            "e": float(map_region["e"]) + E_shift,
            "w": float(map_region["w"]) + E_shift,
        }

        shifts.append(tuple(E_shift, N_shift))
        heights.append(height)
        height = height + height_steps

        overlap_areas.append(get_overlap(tempname, dark_pixels, map_region, new_region))

    # Find the maximum overlapping area between clouds and dark_pixels
    index_max_overlap = numpy.argmax(overlap_areas)

    gscript.verbose(
        "--- the estimated clouds height is: {} m ---".format(heights[index_maxAA])
    )
    gscript.verbose(
        "--- the estimated east shift is: {:.2f} m ---".format(dE[index_maxAA])
    )
    gscript.verbose(
        "--- the estimated north shift is: {:.2f} m ---".format(dN[index_maxAA])
    )

    # Clouds are shifted using the clouds height corresponding to the
    # maximum overlapping area then are intersect with dark_pixels
    gscript.run_command(
        "r.region",
        map=tempname,
        n=float(map_region["n"]) + shifts[index_max_overlap][1],
        s=float(map_region["s"]) + shifts[index_max_overlap][1],
        e=float(map_region["e"]) + shifts[index_max_overlap][0],
        w=float(map_region["w"]) + shifts[index_max_overlap][0],
    )

    gscript.mapcalc(
        "{0}=if(isnull({1}),if(isnull({2}),if(isnull({3}),null(),3),2),1)".format(
            output, cloud, tempname, shadow
        )
    )

    gscript.raster_history(output)


def cleanup():
    gscript.run_command(
        "g.remove", flags="f", type="raster", pattern="{}*".format(tempname), quiet=True
    )


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
