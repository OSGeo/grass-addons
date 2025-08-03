#!/usr/bin/env python

#
##############################################################################
#
# MODULE:       r.divergence
#
# AUTHOR(S):    Anna Petrasova (kratochanna gmail.com)
#
# PURPOSE:      Implementation of divergence of field
#
# COPYRIGHT:    (C) 2015 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (version 2). Read the file COPYING that comes with GRASS
# 		for details.
#
##############################################################################

# %module
# % description: Computes divergence of a vector field defined by magnitude and direction
# % keyword: raster
# % keyword: divergence
# %end
# %option G_OPT_R_INPUT
# % key: magnitude
# % description: Name of input raster map representing magnitude
# %end
# %option G_OPT_R_INPUT
# % label:  Name of input raster map representing direction
# % description: Direction is in degrees ccw from the east
# % key: direction
# %end
# %option G_OPT_R_OUTPUT
# % description: Name of output divergence raster
# %end


import sys
import os
import atexit

from grass.exceptions import CalledModuleError
import grass.script.core as gcore
import grass.script.raster as grast


TMP = []
CLEANUP = True


def cleanup():
    if CLEANUP:
        gcore.run_command("g.remove", flags="f", type="raster", name=TMP, quiet=True)


def main():
    magnitude = options["magnitude"]
    direction = options["direction"]
    divergence = options["output"]
    global TMP, CLEANUP

    tmp_name = "tmp_divergence_" + str(os.getpid())
    qsx = tmp_name + "qsx"
    qsy = tmp_name + "qsy"
    qsx_dx = tmp_name + "qsx_dx"
    qsy_dy = tmp_name + "qsy_dy"
    TMP.extend([qsx, qsy, qsx_dx, qsy_dy])

    # checks if there are already some maps
    old_maps = temp_maps_exist()
    if old_maps:
        if not gcore.overwrite():
            CLEANUP = False
            gcore.fatal(
                _(
                    "You have to first check overwrite flag or remove"
                    " the following maps:\n"
                    "names}"
                ).format(names=",".join(old_maps))
            )
        else:
            gcore.warning(
                _("The following maps will be overwritten: {names}").format(
                    names=",".join(old_maps)
                )
            )
    try:
        grast.mapcalc(
            exp="{qsx}={mag} * cos({direct})".format(
                qsx=qsx, mag=magnitude, direct=direction
            )
        )
        grast.mapcalc(
            exp="{qsy}={mag} * sin({direct})".format(
                qsy=qsy, mag=magnitude, direct=direction
            )
        )
        gcore.run_command("r.slope.aspect", elevation=qsx, dx=qsx_dx)
        gcore.run_command("r.slope.aspect", elevation=qsy, dy=qsy_dy)
        grast.mapcalc(
            exp="{div}={qsx_dx} + {qsy_dy}".format(
                div=divergence, qsx_dx=qsx_dx, qsy_dy=qsy_dy
            )
        )
    except CalledModuleError:
        gcore.fatal(
            _(
                "r.divergence failed, check errors above. Please report this problem to developers."
            )
        )
        return 1

    grast.raster_history(divergence)
    return 0


def temp_maps_exist():
    maps = gcore.list_grouped("raster")[gcore.gisenv()["MAPSET"]]
    return [x for x in TMP if x in maps]


if __name__ == "__main__":
    options, flags = gcore.parser()
    atexit.register(cleanup)
    sys.exit(main())
