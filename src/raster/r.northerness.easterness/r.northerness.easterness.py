#!/usr/bin/env python

"""
MODULE:    r.northerness.easterness

AUTHOR(S): Helmut Kudrnovsky <alectoria AT gmx at>

PURPOSE:   Calculates northerness and easterness of a DEM

COPYRIGHT: (C) 2014 by the GRASS Development Team

           This program is free software under the GNU General Public
           License (>=v2). Read the file COPYING that comes with GRASS
           for details.
"""

# %module
# % description: Calculation of northerness, easterness and the interaction between northerness and slope
# % keyword: raster
# % keyword: terrain
# % keyword: aspect
# % keyword: slope
# % keyword: sun
# %end

# %option G_OPT_R_ELEV
# % key: elevation
# % description: Name of elevation raster map
# % required: yes
# %end

import sys
import os
import grass.script as grass
import math


def main():
    r_elevation = options["elevation"].split("@")[0]
    r_aspect = r_elevation + "_aspect"
    r_slope = r_elevation + "_slope"
    r_aspect_compass = r_elevation + "_aspect_compass"
    r_northerness = r_elevation + "_northerness"
    r_easterness = r_elevation + "_easterness"
    r_northerness_slope = r_elevation + "_northerness_slope"

    # Calculation of slope and aspect maps
    grass.message("----")
    grass.message("Calculation of slope and aspect by r.slope.aspect ...")
    grass.run_command(
        "r.slope.aspect",
        elevation=r_elevation,
        slope=r_slope,
        aspect=r_aspect,
        overwrite=True,
    )
    grass.message("Calculation of slope and aspect done.")
    grass.message("----")

    # Correction aspect angles from cartesian (GRASS default) to compass angles
    #   if((A < 90, 90-A, 360+90-A))
    grass.message(
        "Convert aspect angles from cartesian (GRASS GIS default) to compass angles ..."
    )
    grass.mapcalc(
        "$outmap = if( $cartesian == 0, 0, if( $cartesian < 90, 90 - $cartesian, 360 + 90 - $cartesian) )",
        outmap=r_aspect_compass,
        cartesian=r_aspect,
    )
    grass.message("...")
    grass.run_command("r.info", map=r_aspect_compass)
    grass.message("Aspect conversion done.")
    grass.message("----")

    # Calculation of northerness
    grass.message("Calculate northerness ...")
    grass.mapcalc(
        "$outmap = cos( $compass )", outmap=r_northerness, compass=r_aspect_compass
    )
    grass.message("...")
    grass.run_command("r.info", map=r_northerness)
    grass.message("Northerness calculation done.")
    grass.message("----")

    # Calculation of easterness
    grass.message("Calculate easterness ...")
    grass.mapcalc(
        "$outmap = sin( $compass )", outmap=r_easterness, compass=r_aspect_compass
    )
    grass.message("...")
    grass.run_command("r.info", map=r_easterness)
    grass.message("Easterness calculation done.")
    grass.message("----")

    # Calculation of northerness*slope
    grass.message("Calculate northerness*slope ...")
    grass.mapcalc(
        "$outmap = $northerness * $slope",
        outmap=r_northerness_slope,
        northerness=r_northerness,
        slope=r_slope,
    )
    grass.message("...")
    grass.run_command("r.info", map=r_northerness_slope)
    grass.message("Northerness*slope calculation done.")
    grass.message("----")

    # adjust color
    grass.message("Adjust color ...")
    grass.run_command("r.colors", map=r_northerness, color="grey")
    grass.run_command("r.colors", map=r_easterness, color="grey")
    grass.run_command("r.colors", map=r_northerness_slope, color="grey")

    grass.message("Color adjustment done.")
    grass.message("----")

    # clean up some temporay files and maps
    grass.message("Some clean up ...")
    grass.run_command("g.remove", flags="f", type="raster", name=r_slope, quiet=True)
    grass.run_command("g.remove", flags="f", type="raster", name=r_aspect, quiet=True)
    grass.run_command(
        "g.remove", flags="f", type="raster", name=r_aspect_compass, quiet=True
    )
    grass.message("Clean up done.")
    grass.message("----")

    # r.northerness.easterness done!
    grass.message("r.northerness.easterness done!")


if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
