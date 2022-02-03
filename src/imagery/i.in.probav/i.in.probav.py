#!/usr/bin/env python
############################################################################
#
# MODULE:       i.in.probav
# AUTHOR(S):    Jonas Strobel, intern at mundialis and terrestris, Bonn
# PURPOSE:      i.in.probav
# COPYRIGHT:    (C) 2017 by stjo, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % description: Imports PROBA-V NDVI data in netCDF format into a raster map with real NDVI data range.
# % keyword: imagery
# % keyword: import
# % keyword: NDVI
# % keyword: PROBA-V
# %end
# %option G_OPT_F_INPUT
# % description: Name of input PROBA-V NDVI .nc file
# %end
# %option G_OPT_R_OUTPUT
# %end
# %option
# % key: scale
# % type: double
# % required: no
# % multiple: no
# % answer: 0.004
# % key_desc: float
# % description: Scale factor for input
# %end
# %option
# % key: shift
# % type: double
# % required: no
# % multiple: no
# % answer: -0.08
# % key_desc: float
# % label: Shift factor for input
# % description: Offset factor for input
# %end
# %option
# % key: memory
# % type: double
# % required: no
# % multiple: no
# % options: 0-2047
# % answer: 300
# % key_desc: integer
# % description: Maximum memory to be used in MB
# %end

import sys
import os
import atexit
import grass.script as gscript
from grass.exceptions import CalledModuleError


def cleanup():
    pass


def main():

    global tmpfile
    infile = options["input"]
    out = options["output"]
    scale = options["scale"]
    offset = options["shift"]
    mem = options["memory"]

    pid = os.getpid()
    tmpname = str(pid) + "i.in.probav"
    tmpfile = gscript.tempfile()

    if not gscript.overwrite() and gscript.find_file(out)["file"]:
        gscript.fatal(("<%s> already exists. Aborting.") % out)

    # Are we in LatLong location?
    s = gscript.read_command("g.proj", flags="j")
    kv = gscript.parse_key_val(s)
    if kv["+proj"] != "longlat":
        gscript.fatal(("This module only operates in LatLong locations"))

    try:
        gscript.message("Importing raster map <" + out + ">...")
        gscript.run_command(
            "r.in.gdal", input=infile, output=tmpname, memory=mem, quiet=True
        )
    except CalledModuleError:
        gscript.fatal(("An error occurred. Stop."))

    # What is the relation between the digital number and the real NDVI ?
    # Real NDVI =coefficient a * Digital Number + coefficient b
    #           = a * DN +b
    #
    # Coefficient a = scale
    # Coefficient b = offset

    # create temporary region
    gscript.use_temp_region()
    gscript.run_command("g.region", raster=tmpname, quiet=True)
    gscript.message("Remapping digital numbers to NDVI...")

    # do the mapcalc
    gscript.mapcalc(
        "${out} = ${a} * ${tmpname} + ${b}", out=out, a=scale, tmpname=tmpname, b=offset
    )

    # remove original input
    gscript.run_command("g.remove", type="raster", name=tmpname, quiet=True, flags="f")

    # set color table to ndvi
    gscript.run_command("r.colors", map=out, color="ndvi")

    gscript.message(("Done: generated map <%s>") % out)

    return 0


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
