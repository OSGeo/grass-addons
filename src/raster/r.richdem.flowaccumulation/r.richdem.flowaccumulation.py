#!/usr/bin/env python
############################################################################
#
# MODULE:       r.richdem.flowaccumulation
#
# AUTHOR(S):    Richard Barnes, Andrew Wickert
#
# PURPOSE:      Calculates flow accumulation via one of a variety of methods.
#
# COPYRIGHT:    (c) 2019 Andrew Wickert; RichDEM is (c) 2015 Richard Barnes
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS: richdem

# More information
# Started June 2019

# %module
# % description: Calculates flow accumulation via one of a variety of methods.
# % keyword: raster
# % keyword: hydrology
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  label: Input DEM
# %  required: yes
# %end

# %option G_OPT_R_INPUT
# %  key: weights
# %  label: Raster defining the amount of runoff per cell
# %  required: no
# %end

# %option
# % key: method
# % type: string
# % label: Method to compute the flow routing.
# % required: yes
# % multiple: no
# % options: Dinf,Quinn,Holmgren,Freeman,Rho8,Rho4,D8,D4
# %end

# %option
# % key: exponent
# % type: double
# % label: Exponent required for Holmgren and Freeman methods
# % required: no
# % multiple: no
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  label: Output DEM with depressions filled
# %  required: yes
# %end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np

# GRASS
from grass import script as gscript
from grass.script import array as garray
from grass.pygrass.modules.shortcuts import general as g

###############
# MAIN MODULE #
###############


def main():
    """
    RichDEM flat resolution: give a gentle slope
    """
    # lazy import RICHDEM
    try:
        import richdem as rd
    except:
        g.message(
            flags="e",
            message=(
                "RichDEM not detected. Install pip3 and "
                + "then type at the command prompt: "
                + '"pip3 install richdem".'
            ),
        )

    _input = options["input"]
    _output = options["output"]
    _method = options["method"]
    _exponent = options["exponent"]
    _weights = options["weights"]

    if (_method == "Holmgren") or (_method == "Freeman"):
        if _exponent == "":
            g.message(
                flags="w",
                message=(
                    "Exponent must be defined for "
                    + "Holmgren or Freeman methods. "
                    + "Exiting."
                ),
            )
            return
        else:
            _exponent = float(_exponent)
    else:
        _exponent = None

    if _weights == "":
        rd_weights = None
    else:
        g_weights = garray.array(_weights, null=np.nan)
        rd_weights = rd.rdarray(g_weights, no_data=np.nan)

    dem = garray.array(_input, null=np.nan)

    mask = dem * 0 + 1

    rd_input = rd.rdarray(dem, no_data=np.nan)
    del dem
    rd_output = rd.FlowAccumulation(
        dem=rd_input,
        method=_method,
        exponent=_exponent,
        weights=rd_weights,
        in_place=False,
    )

    rd_output *= mask

    accum = garray.array()
    accum[:] = rd_output[:]
    accum.write(_output, overwrite=gscript.overwrite())


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
