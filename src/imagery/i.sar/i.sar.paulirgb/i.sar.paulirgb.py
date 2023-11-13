#!/usr/bin/env python3

############################################################################
#
# MODULE:	i.sar.paulirgb
#
# AUTHOR:   Santiago Seppi
#
# PURPOSE:	Create the RGB bands for the Pauli combination
#
# COPYRIGHT: (C) 2002-2023 by the GRASS Development Team
#
# 		This program is free software under the GNU General Public
# 		License (>=v2). Read the file COPYING that comes with GRASS
# 		for details.
#
#
#############################################################################

# %Module
# % description: Create the RGB bands for the Pauli combination.
# % keyword: imagery
# % keyword: sar
# % keyword: radar
# % keyword: rgb
# % overwrite: yes
# %End
# %option G_OPT_R_INPUT
# % key: hh
# % description: HH polarization band
# %end
# %option G_OPT_R_INPUT
# % key: vv
# % description: VV polarization band
# %end
# %option G_OPT_R_INPUT
# % key: hv
# % description: HV polarization band
# %end
# %option G_OPT_R_OUTPUT
# % key: basename
# % description: Prefix for output raster maps
# % required: yes
# %end
# %option
# % key: strength
# % type: double
# % description: Cropping intensity (upper brightness level)
# % options: 0-100
# % required: no
# %end

import subprocess
import sys

import grass.script as gs


def main():
    hh = options["hh"]
    vv = options["vv"]
    hv = options["hv"]
    basename = options["basename"]
    strength = options["strength"]
    pauli_red = f"{basename}_Pauli_Red = {hh}-{vv}"
    gs.mapcalc(exp=pauli_red)
    pauli_green = f"{basename}_Pauli_Green = 2*{hv}"
    gs.mapcalc(exp=pauli_green)
    pauli_blue = f"{basename}_Pauli_Blue = {hh}+{vv}"
    gs.mapcalc(exp=pauli_blue)

    if strength:
        gs.run_command(
            "i.colors.enhance",
            red=f"{basename}_Pauli_Red",
            green=f"{basename}_Pauli_Green",
            blue=f"{basename}_Pauli_Blue",
            strength=strength,
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    main()
