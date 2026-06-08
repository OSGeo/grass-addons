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
import numpy as np

# GRASS
import grass.script as gs


def main():
    """
    Compute cell areas
    """

    projinfo = gs.parse_command("g.proj", flags="g")

    options, flags = gs.parser()
    output = options["output"]
    units = options["units"]

    # First check if output exists
    if len(gs.parse_command("g.list", type="rast", pattern=options["output"])):
        if not gs.overwrite():
            gs.fatal(
                "Raster map '"
                + options["output"]
                + "' already exists. Use '--o' to overwrite."
            )

    projunits = str(projinfo.get("units", ""))

    if projunits.lower() in ("degrees", "degree"):
        if units == "m2":
            gs.mapcalc(
                "{out} = ( 111195. * nsres() )"
                " * ( ewres() * {rad} * 6371000. * cos(y()) )".format(
                    out=output, rad=np.pi / 180.0
                )
            )
        elif units == "km2":
            gs.mapcalc(
                "{out} = ( 111.195 * nsres() )"
                " * ( ewres() * {rad} * 6371. * cos(y()) )".format(
                    out=output, rad=np.pi / 180.0
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
        if units == "m2":
            gs.mapcalc("{out} = nsres() * ewres() * {m2}".format(out=output, m2=m**2))
        elif units == "km2":
            gs.mapcalc(
                "{out} = nsres() * ewres() * {m2} / 1.e6".format(out=output, m2=m**2)
            )


if __name__ == "__main__":
    main()
