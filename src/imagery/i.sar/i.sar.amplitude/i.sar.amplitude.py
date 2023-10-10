#!/usr/bin/env python3

############################################################################
#
# MODULE:	i.sar.amplitude
#
# AUTHOR:   Santiago Seppi
#
# PURPOSE:	Computation of amplitude map for SLC complex SAR image
#
# COPYRIGHT: (C) 2002-2023 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#
#############################################################################

# %module
# % description: Calculates amplitude for SAR image
# %end
# %option G_OPT_R_INPUT
# % key: real
# % description: Name of real band
# %end
# %option G_OPT_R_INPUT
# % key: imag
# % description: Name of imaginary band
# %end
# %option G_OPT_R_OUTPUT
# % key: output
# %end

import subprocess
import sys

import grass.script as gs


def main():
    options, flags = gs.parser()
    real = options["real"]
    imag = options['imag']
    raster_output = options["output"]
    amplitude_formula = f'{raster_output} = sqrt(pow({real},2) + pow({imag},2))'

    gs.mapcalc(exp=amplitude_formula)


if __name__ == "__main__":
    main()
