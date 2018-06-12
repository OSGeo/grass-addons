#!/usr/bin/env python
############################################################################
#
# MODULE:       r.lfp
# AUTHOR(S):    Huidae Cho
# PURPOSE:      Calculates the longest flow path for a given outlet point.
#
# COPYRIGHT:    (C) 2014, 2017, 2018 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%module
#% description: Calculates the longest flow path for a given outlet point using the r.stream.distance addon.
#% keyword: hydrology
#% keyword: watershed
#%end
#%option G_OPT_R_INPUT
#% description: Name of input drainage direction raster map
#%end
#%option G_OPT_V_OUTPUT
#% description: Name for output longest flow path vector map
#%end
#%option G_OPT_M_COORDS
#% description: Coordinates of outlet point
#% multiple: yes
#%end
#%option G_OPT_V_INPUT
#% key: outlet
#% label: Name of outlet vector map
#% required: no
#%end
#%rules
#% required: coordinates, outlet
#%end

import sys
import os
import grass.script as grass
from grass.exceptions import CalledModuleError


# check requirements
def check_progs():
    found_missing = False
    prog = "r.stream.distance"
    if not grass.find_program(prog, "--help"):
        found_missing = True
        grass.warning(_("'%s' required. Please install '%s' first using 'g.extension %s'") % (prog, prog, prog))
    if found_missing:
        grass.fatal(_("An ERROR occurred running r.lfp"))

def main():
    # check dependencies
    check_progs()

    input = options["input"]
    output = options["output"]
    coords = options["coordinates"]
    outlet = options["outlet"]

    calculate_lfp(input, output, coords, outlet)

def calculate_lfp(input, output, coords, outlet):
    prefix = "r_lfp_%d_" % os.getpid()

    # create the output vector map
    try:
        grass.run_command("v.edit", map=output, tool="create")
    except CalledModuleError:
        grass.fatal(_("Cannot create the output vector map"))

    if coords:
        coords = coords.split(",")
    else:
        coords = []

    # append outlet points to coordinates
    if outlet:
        p = grass.pipe_command("v.to.db", flags="p", map=outlet, option="coor")
        for line in p.stdout:
            line = line.rstrip("\n")
            if line == "cat|x|y|z":
                continue
            cols = line.split("|")
            coords.extend([cols[1], cols[2]])
        p.wait()
        if p.returncode != 0:
            grass.fatal(_("Cannot read outlet points"))

    for i in range(0, len(coords) / 2):
        coor = "%s,%s" % (coords[2*i], coords[2*i+1])
        grass.message(_("Processing the outlet at %s..." % coor))

        # create the outlet vector map
        out = prefix + "out"
        p = grass.feed_command("v.in.ascii", overwrite=True,
                input="-", output=out, separator=",")
        p.stdin.write(coor)
        p.stdin.close()
        p.wait()
        if p.returncode != 0:
            grass.fatal(_("Cannot create the outlet vector map"))

        # convert the outlet vector map to raster
        try:
            grass.run_command("v.to.rast", overwrite=True,
                              input=out, output=out, use="cat",
                              type="point")
        except CalledModuleError:
            grass.fatal(_("Cannot convert the outlet vector to raster"))

        # calculate the downstream flow length
        flds = prefix + "flds"
        try:
            grass.run_command("r.stream.distance", overwrite=True, flags="om",
                              stream_rast=out, direction=input,
                              method="downstream", distance=flds)
        except CalledModuleError:
            grass.fatal(_("Cannot calculate the downstream flow length"))

        # find the longest flow length
        p = grass.pipe_command("r.info", flags="r", map=flds)
        max = ""
        for line in p.stdout:
            line = line.rstrip("\n")
            if line.startswith("max="):
                max = line.split("=")[1]
                break
        p.wait()
        if p.returncode != 0 or max == "":
            grass.fatal(_("Cannot find the longest flow length"))

        threshold = float(max) - 0.0005

        # find the headwater cells
        heads = prefix + "heads"
        try:
            grass.run_command("r.mapcalc", overwrite=True,
                              expression="%s=if(%s>=%f,1,null())" %
                                         (heads, flds, threshold))
        except CalledModuleError:
            grass.fatal(_("Cannot find the headwater cells"))

        # create the headwater vector map
        try:
            grass.run_command("r.to.vect", overwrite=True,
                              input=heads, output=heads, type="point")
        except CalledModuleError:
            grass.fatal(_("Cannot create the headwater vector map"))

        # calculate the longest flow path in vector format
        path = prefix + "path"
        try:
            grass.run_command("r.path", input=input, vector_path=path,
                              start_points=heads)
        except CalledModuleError:
            grass.fatal(_("Cannot create the longest flow path vector map"))

        # snap the outlet
        try:
            grass.run_command("r.to.vect", overwrite=True,
                              input=out, output=out, type="point")
        except CalledModuleError:
            grass.fatal(_("Cannot snap the outlet"))

        # find the coordinates of the snapped outlet
        p = grass.pipe_command("v.to.db", flags="p", map=out, option="coor")
        coor = ""
        for line in p.stdout:
            line = line.rstrip("\n")
            if line == "cat|x|y|z":
                continue
            cols = line.split("|")
            coor = "%s,%s" % (cols[1], cols[2])
        p.wait()
        if p.returncode != 0 or coor == "":
            grass.fatal(_("Cannot find the coordinates of the snapped outlet"))

        # split the longest flow path at the outlet
        try:
            grass.run_command("v.edit", map=path, tool="break", coords=coor)
        except CalledModuleError:
            grass.fatal(_("Cannot split the longest flow path at the outlet"))

        # select the final longest flow path
        lfp = prefix + "lfp"
        try:
            grass.run_command("v.select", overwrite=True,
                              ainput=path, binput=heads, output=lfp)
        except CalledModuleError:
            grass.fatal(_("Cannot select the final longest flow path"))

        # copy the final longest flow path to the output map
        try:
            grass.run_command("v.edit", flags="r",
                              map=output, tool="copy", bgmap=lfp, cats=0)
        except CalledModuleError:
            grass.fatal(_("Cannot copy the final longest flow path"))

    # remove intermediate outputs
    grass.run_command("g.remove", flags="f", type="raster,vector",
                      pattern="%s*" % prefix)

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
