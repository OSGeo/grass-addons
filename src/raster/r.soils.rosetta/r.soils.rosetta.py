#!/usr/bin/env python

##############################################################################
# MODULE:    r.soils.rosetta
#
# AUTHOR(S): Corey T. White <corey.white@openplains.com>
#
# PURPOSE:   Estimate van Genuchten soil hydraulic parameters from soil texture using the ROSETTA pedotransfer model.
#
# COPYRIGHT: (C) 2026 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
##############################################################################

"""Estimate van Genuchten soil hydraulic parameters from soil texture using the ROSETTA pedotransfer model."""

# %module
# % description: Estimate van Genuchten soil hydraulic parameters from soil texture using the ROSETTA pedotransfer model.
# % keyword: raster
# % keyword: algebra
# % keyword: random
# %end
# %option G_OPT_R_INPUT
# %end
# %option G_OPT_R_OUTPUT
# %end

import sys
import atexit
from gettext import gettext as _
import grass.script as gs
from grass.tools import Tools


def clean(name):
    gs.run_command("g.remove", type="raster", name=name, flags="f", superquiet=True)


def main():

    # initalize tools
    tools = Tools()

    # get input options
    options, flags = gs.parser()
    input_raster = options["input"]
    output_raster = options["output"]

    # crete a temporary raster that will be removed upon exit
    temporary_raster = gs.append_node_pid("gauss")
    atexit.register(clean, temporary_raster)

    # if changing computational region is needed, uncomment
    # Use RegionManager/MaskManager as context managers for temporary region/mask:
    # They automatically restore the previous region/mask on exit.
    # Example:
    # with gs.RegionManager():          # temporarily set computational region
    #     with gs.MaskManager():        # temporarily set raster/vector mask
    #         # perform region/mask-specific operations here
    #         pass

    # verbose message with translatable string
    gs.verbose(_("Generating temporary raster {tmp}").format(tmp=temporary_raster))

    # run analysis
    tools.r_surf_gauss(output=temporary_raster)
    tools.r_mapcalc(expression=f"{output_raster} = {input_raster} + {temporary_raster}")

    # save history into the output raster
    gs.raster_history(output_raster, overwrite=True)


if __name__ == "__main__":
    sys.exit(main())
