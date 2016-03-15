#!/usr/bin/env python
############################################################################
#
# MODULE:       v.lfp
# AUTHOR(S):    Huidae Cho
# PURPOSE:      Converts a longest flow path raster map created by r.lfp to
#               a vector map.
#
# COPYRIGHT:    (C) 2014 by the GRASS Development Team
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
    p = grass.pipe_command("r.info", flags="g", map=input)
    res = ""
    for line in p.stdout:
        line = line.rstrip("\n")
        if line.startswith("nsres="):
            res = line.split("=")[1]
            break
    p.wait()
    if p.returncode != 0 or res == "":
        grass.fatal(_("Cannot read the resolution of int input raster map"))
    res = float(res)
    danglelen = math.ceil(math.sqrt(2)*res)

    try:
        grass.run_command("r.to.vect", input=input, output=output, type="line")
    except CalledModuleError:
        grass.fatal(_("Cannot convert the input raster map to a vector map"))

    try:
        grass.run_command("v.edit", map=output, tool="delete",
                          query="dangle", threshold="0,0,-%f" % danglelen)
    except CalledModuleError:
        grass.fatal(_("Cannot delete dangles from the output vector map"))

    success = False
    for i in range(0, 100):
        try:
            grass.run_command("v.edit", map=output, tool="merge", where="")
        except CalledModuleError:
            grass.fatal(_("Cannot merge features in the output vector map"))

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
            grass.fatal(_("Cannot process the output vector map"))
        elif lines == 1:
            success = True
            break

        p = grass.pipe_command("v.report", map=output, option="length",
                sort="asc")
        firstcat = ""
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("cat|value|"):
                continue
            cols = line.split("|")
            firstcat = cols[0]
            break
        p.wait()
        if p.returncode != 0:
            grass.fatal(_("Cannot read the output vector map report"))

        if firstcat == "":
            grass.fatal(_("Cannot further simplify the longest flow path"))

        try:
            grass.run_command("v.edit", map=output, tool="delete",
                              cats=firstcat)
        except CalledModuleError:
            grass.fatal(_("Cannot delete short segments from the output vector map"))

    if success == False:
        grass.fatal(_("Cannot simplify the longest flow path"))

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


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
