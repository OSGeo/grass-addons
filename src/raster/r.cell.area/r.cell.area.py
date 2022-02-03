#! /usr/bin/env python

############################################################################
#
# MODULE:       r.cell.area
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Compute raster cell areas
#
# COPYRIGHT:    (c) 2017 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#

# %module
# % description: Calculate cell sizes within the computational region
# % keyword: raster
# % keyword: statistics
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  type: string
# %  description: Output grid of cell sizes
# %  required: yes
# %end

# %option
# %  key: units
# %  type: string
# %  description: Units for output areas
# %  options: m2, km2
# %  required: yes
# %end

##################
# IMPORT MODULES #
##################

# PYTHON
import os
import glob
import numpy as np

# GRASS
import grass.script as grass
from grass.script import array as garray
from grass.pygrass.vector import VectorTopo


def main():
    """
    Compute cell areas
    """

    projinfo = grass.parse_command("g.proj", flags="g")

    options, flags = grass.parser()
    output = options["output"]
    units = options["units"]

    # First check if output exists
    if len(grass.parse_command("g.list", type="rast", pattern=options["output"])):
        if not grass.overwrite():
            grass.fatal(
                "Raster map '"
                + options["output"]
                + "' already exists. Use '--o' to overwrite."
            )

    projunits = str(projinfo["units"])  # Unicode to str
    # Then compute
    if (projunits == "meters") or (projunits == "Meters"):
        if units == "m2":
            grass.mapcalc(output + " = nsres() * ewres()")
        elif units == "km2":
            grass.mapcalc(output + " = nsres() * ewres() / 10.^6")
    elif (projunits == "degrees") or (projunits == "Degrees"):
        if units == "m2":
            grass.mapcalc(
                output
                + " = ( 111195. * nsres() ) * \
                          ( ewres() * "
                + str(np.pi / 180.0)
                + " * 6371000. * cos(y()) )"
            )
        elif units == "km2":
            grass.mapcalc(
                output
                + " = ( 111.195 * nsres() ) * \
                          ( ewres() * "
                + str(np.pi / 180.0)
                + " * 6371. * cos(y()) )"
            )
    else:
        print("Units: ", projunits, " not currently supported")


if __name__ == "__main__":
    main()
