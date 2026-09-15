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
# SPDX-FileCopyrightText: 2017 Andrew Wickert
# SPDX-License-Identifier: GPL-2.0-or-later

# %module
# % description: Calculates the area of each raster cell for the computational region
# % keyword: raster
# % keyword: geometry
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  label: Output raster of cell areas
# %  description: Name of output raster map containing cell areas
# %  required: yes
# %end

# %option
# %  key: units
# %  type: string
# %  label: Output units
# %  description: Units for output cell areas
# %  options: m2, km2, ha, acres, mi2
# %  descriptions: m2;Square meters;km2;Square kilometers;ha;Hectares;acres;Acres;mi2;Square miles
# %  required: yes
# %end

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
    options, flags = gs.parser()
    output = options["output"]
    units = options["units"]

    projinfo = gs.parse_command("g.proj", flags="g")

    if not str(projinfo.get("units", "")):
        gs.fatal(_("Projection units are unknown; XY locations are not supported"))

    factor = _M2_TO_UNIT[units]
    gs.warning(_("r.cell.area is deprecated; use r.mapcalc area() instead"))
    gs.mapcalc(f"{output} = area() * {factor}")


if __name__ == "__main__":
    main()
