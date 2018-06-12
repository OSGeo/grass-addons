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
#% required: yes
#%end

import sys
import os
import grass.script as grass
from grass.exceptions import CalledModuleError


# check requirements
def check_progs():
    found_missing = False
    prog = 'r.stream.distance'
    if not grass.find_program(prog, '--help'):
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

    calculate_lfp(input, output, coords)

def calculate_lfp(input, output, coords):
    prefix = "r_lfp_%d_" % os.getpid()

    # create the outlet vector map
    outlet = prefix + "outlet"
    p = grass.feed_command("v.in.ascii", overwrite=True,
            input="-", output=outlet, separator=",")
    p.stdin.write(coords)
    p.stdin.close()
    p.wait()
    if p.returncode != 0:
        grass.fatal(_("Cannot create the outlet vector map"))

    # convert the outlet vector map to raster
    try:
        grass.run_command("v.to.rast", overwrite=True,
                          input=outlet, output=outlet, use="cat", type="point")
    except CalledModuleError:
        grass.fatal(_("Cannot convert the outlet vector to raster"))

    # calculate the downstream flow length
    flds = prefix + "flds"
    try:
        grass.run_command("r.stream.distance", overwrite=True, flags="om",
                          stream_rast=outlet, direction=input,
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
                          input=outlet, output=outlet, type="point")
    except CalledModuleError:
        grass.fatal(_("Cannot snap the outlet"))

    # find the coordinates of the snapped outlet
    p = grass.pipe_command("v.to.db", flags="p", map=outlet, option="coor")
    coords = ""
    for line in p.stdout:
        line = line.rstrip("\n")
        if line == "cat|x|y|z":
            continue
        cols = line.split("|")
        coords = "%s,%s" % (cols[1], cols[2])
    p.wait()
    if p.returncode != 0 or coords == "":
        grass.fatal(_("Cannot find the coordinates of the snapped outlet"))

    # split the longest flow path at the outlet
    try:
        grass.run_command("v.edit", map=path, tool="break", coords=coords)
    except CalledModuleError:
        grass.fatal(_("Cannot split the longest flow path at the outlet"))

    # select the final longest flow path
    try:
        grass.run_command("v.select", overwrite=True,
                          ainput=path, binput=heads, output=output)
    except CalledModuleError:
        grass.fatal(_("Cannot select the final longest flow path"))

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
