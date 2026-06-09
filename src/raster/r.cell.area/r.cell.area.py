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
# %  options: m2, km2, ha, acres, mi2
# %  descriptions: m2;Square meters;km2;Square kilometers;ha;Hectares;acres;Acres;mi2;Square miles
# %  required: yes
# %end

##################
# IMPORT MODULES #
##################

# PYTHON
import math

# GRASS
import grass.script as gs


# Conversion factors from m² — values match GRASS G_meters_to_units_factor_sq()
_M2_TO_UNIT = {
    "m2": 1.0,
    "km2": 1.0e-6,
    "ha": 1.0e-4,
    "acres": 1.0 / 4046.8564224,
    "mi2": 1.0 / 2589988.110336,
}


def main():
    """
    Compute cell areas
    """

    options, flags = gs.parser()
    output = options["output"]
    units = options["units"]

    projinfo = gs.parse_command("g.proj", flags="g")

    projunits = str(projinfo.get("units", ""))
    factor = _M2_TO_UNIT[units]

    if projunits.lower() in ("degrees", "degree"):
        rad = math.pi / 180.0
        gs.mapcalc(
            "{out} = ( 111195. * nsres() )"
            " * ( ewres() * {rad} * 6371000. * cos(y()) ) * {f}".format(
                out=output, rad=rad, f=factor
            )
        )
    elif not projunits:
        gs.fatal(_("Projection units are unknown; XY locations are not supported"))
    else:
        # Any projected CRS: use the meters-per-map-unit conversion factor so
        # that feet, US survey feet, and all other linear units work correctly.
        m = float(projinfo.get("meters", 0))
        if m <= 0:
            gs.fatal(_("Projection units '%s' are not supported") % projunits)
        gs.mapcalc(
            "{out} = nsres() * ewres() * {coeff}".format(
                out=output, coeff=m**2 * factor
            )
        )


if __name__ == "__main__":
    main()
