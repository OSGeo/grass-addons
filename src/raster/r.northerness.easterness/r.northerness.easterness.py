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
import grass.script as gs
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
    gs.message("----")
    gs.message("Calculation of slope and aspect by r.slope.aspect ...")
    gs.run_command(
        "r.slope.aspect",
        elevation=r_elevation,
        slope=r_slope,
        aspect=r_aspect,
        overwrite=True,
    )
    gs.message("Calculation of slope and aspect done.")
    gs.message("----")

    # Correction aspect angles from cartesian (GRASS default) to compass angles
    #   if((A < 90, 90-A, 360+90-A))
    gs.message(
        "Convert aspect angles from cartesian (GRASS GIS default) to compass angles ..."
    )
    gs.mapcalc(
        "$outmap = if( $cartesian == 0, 0, if( $cartesian < 90, 90 - $cartesian, 360 + 90 - $cartesian) )",
        outmap=r_aspect_compass,
        cartesian=r_aspect,
    )
    gs.message("...")
    gs.run_command("r.info", map=r_aspect_compass)
    gs.message("Aspect conversion done.")
    gs.message("----")

    # Calculation of northerness
    gs.message("Calculate northerness ...")
    gs.mapcalc(
        "$outmap = cos( $compass )", outmap=r_northerness, compass=r_aspect_compass
    )
    gs.message("...")
    gs.run_command("r.info", map=r_northerness)
    gs.message("Northerness calculation done.")
    gs.message("----")

    # Calculation of easterness
    gs.message("Calculate easterness ...")
    gs.mapcalc(
        "$outmap = sin( $compass )", outmap=r_easterness, compass=r_aspect_compass
    )
    gs.message("...")
    gs.run_command("r.info", map=r_easterness)
    gs.message("Easterness calculation done.")
    gs.message("----")

    # Calculation of northerness*slope
    gs.message("Calculate northerness*slope ...")
    gs.mapcalc(
        "$outmap = $northerness * $slope",
        outmap=r_northerness_slope,
        northerness=r_northerness,
        slope=r_slope,
    )
    gs.message("...")
    gs.run_command("r.info", map=r_northerness_slope)
    gs.message("Northerness*slope calculation done.")
    gs.message("----")

    # adjust color
    gs.message("Adjust color ...")
    gs.run_command("r.colors", map=r_northerness, color="grey")
    gs.run_command("r.colors", map=r_easterness, color="grey")
    gs.run_command("r.colors", map=r_northerness_slope, color="grey")

    gs.message("Color adjustment done.")
    gs.message("----")

    # clean up some temporay files and maps
    gs.message("Some clean up ...")
    gs.run_command("g.remove", flags="f", type="raster", name=r_slope, quiet=True)
    gs.run_command("g.remove", flags="f", type="raster", name=r_aspect, quiet=True)
    gs.run_command(
        "g.remove", flags="f", type="raster", name=r_aspect_compass, quiet=True
    )
    gs.message("Clean up done.")
    gs.message("----")

    # r.northerness.easterness done!
    gs.message("r.northerness.easterness done!")


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
