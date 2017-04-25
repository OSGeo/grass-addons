#!/usr/bin/env python
############################################################################
#
# MODULE:       v.lfp
# AUTHOR(S):    Huidae Cho
# PURPOSE:      Converts a longest flow path raster map created by r.lfp to
#               a vector map.
#
# COPYRIGHT:    (C) 2014, 2017 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Converts a longest flow path raster map created by r.lfp to a vector map.
#% keyword: hydrology
#% keyword: watershed
#%end
#%option G_OPT_R_INPUT
#% description: Name of input longest flow path raster map
#%end
#%option G_OPT_V_OUTPUT
#% description: Name for output longest flow path vector map
#%end
#%option G_OPT_M_COORDS
#% label: Coordinates of outlet point
#% description: Optionally required to ensure the downstream direction of the output line
#%end

import sys
import os
import math
import grass.script as grass
from grass.exceptions import CalledModuleError


def main():
    input = options["input"]
    output = options["output"]
    coords = options["coordinates"]

    convert_lfp(input, output, coords)

def convert_lfp(input, output, coords):
    # calculate the diagonal resolution
    p = grass.pipe_command("r.info", flags="g", map=input)
    res = ""
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("nsres="):
            res = line.split("=")[1]
            break
    p.wait()
    if p.returncode != 0 or res == "":
        grass.fatal(_("Cannot read the resolution of the input raster map"))
    res = float(res)
    diagres = math.ceil(math.sqrt(2)*res)

    # convert the input lfp raster to vector
    try:
        grass.run_command("r.to.vect", input=input, output=output, type="line")
    except CalledModuleError:
        grass.fatal(_("Cannot convert the input raster map to a vector map"))

    # r.to.vect sometimes produces continous line segments that are not
    # connected; merge them first
    try:
        grass.run_command("v.edit", map=output, tool="merge", where="")
    except CalledModuleError:
        grass.fatal(_("Cannot merge features in the output vector map"))

    # remove dangles
    try:
        grass.run_command("v.edit", map=output, tool="delete",
                          query="dangle", threshold="0,0,-%f" % diagres)
    except CalledModuleError:
        grass.fatal(_("Cannot delete dangles from the output vector map"))

    try:
        grass.run_command("v.edit", map=output, tool="merge", where="")
    except CalledModuleError:
        grass.fatal(_("Cannot merge features in the output vector map"))

    # remove the shorter path from closed loops; these are not dangles
    try:
        grass.run_command("v.edit", map=output, tool="delete",
                          query="length", threshold="0,0,-%f" % diagres)
    except CalledModuleError:
        grass.fatal(_("Cannot delete dangles from the output vector map"))

    try:
        grass.run_command("v.edit", map=output, tool="merge", where="")
    except CalledModuleError:
        grass.fatal(_("Cannot merge features in the output vector map"))

    # see how many lines are left
    p = grass.pipe_command("v.info", flags="t", map=output)
    lines = ""
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("lines="):
            lines = line.split("=")[1]
            break
    p.wait()
    if p.returncode != 0 or lines == "":
        grass.fatal(_("Cannot read lines from the output vector map info"))

    lines = int(lines)
    if lines == 0:
        grass.fatal(_("Cannot create the longest flow path"))
    elif lines > 1:
        grass.fatal(_("Cannot simplify the longest flow path"))

    # leave only the minimum category
    p = grass.pipe_command("v.report", map=output, option="length")
    mincat = ""
    maxcat = ""
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("cat|value|"):
            continue
        cat = line.split("|")[0]
        if mincat == "":
            mincat = cat
        maxcat = cat
    p.wait()
    if p.returncode != 0 or mincat == "" or maxcat == "":
        grass.fatal(_("Cannot read min/max categories from the output vector map"))

    mincat = int(mincat)
    maxcat = int(maxcat)

    try:
        grass.run_command("v.edit", map=output, tool="catdel",
                          cats="%d-%d" % (mincat+1, maxcat), where="")
    except CalledModuleError:
        grass.fatal(_("Cannot delete categories from the output vector map"))

    # if the outlet coordinates are given, flip the longest flow path so that
    # its end node is at the downstream end
    if coords != "":
        p = grass.pipe_command("v.to.db", flags="p", map=output, option="start")
        startx = ""
        starty = ""
        for line in p.stdout:
            line = line.rstrip("\n")
            if line == "cat|x|y|z":
                continue
            cols = line.split("|")
            startx = cols[1]
            starty = cols[2]
        p.wait()
        if p.returncode != 0 or startx == "" or starty == "":
            grass.fatal(_("Cannot read the start point of the longest flow path"))

        startx = float(startx)
        starty = float(starty)

        outxy = coords.split(",")
        outx = float(outxy[0])
        outy = float(outxy[1])

        if startx >= outx - res * 0.5 and startx <= outx + res * 0.5 and \
           starty >= outy - res * 0.5 and starty <= outy + res * 0.5:
            try:
                grass.run_command("v.edit", map=output, tool="flip", where="")
            except CalledModuleError:
                grass.fatal(_("Cannot flip the longest flow path"))

    # write history if supported
    version = grass.version()
    if version["revision"] != "exported":
        # the revision number is available
        version = int(version["revision"][1:])
    else:
        # some binary distributions don't build from the SVN repository and
        # revision is not available; use the libgis revision as a fallback in
        # this case
        version = int(version["libgis_revision"])

    if version >= 70740:
        # v.support -h added in r70740
        grass.run_command("v.support", flags="h", map=output,
                          cmdhist=os.environ["CMDLINE"])


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
