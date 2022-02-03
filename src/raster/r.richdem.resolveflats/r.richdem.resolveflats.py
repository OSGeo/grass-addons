#!/usr/bin/env python
############################################################################
#
# MODULE:       r.richdem.resolveflats
#
# AUTHOR(S):    Richard Barnes, Andrew Wickert
#
# PURPOSE:      Resolves flat areas for continuous downslope flow routing.
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
# % description: Directs flow from flat areas on depression-filled DEMs
# % keyword: raster
# % keyword: hydrology
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  label: Input DEM (most commonly with depressions filled)
# %  required: yes
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  label: Output DEM with flats resolved for continuous flow
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

    # Check for overwrite
    _rasters = np.array(gscript.parse_command("g.list", type="raster").keys())
    if (_rasters == _output).any():
        g.message(flags="e", message="output would overwrite " + _output)

    dem = garray.array(_input, null=np.nan)

    rd_input = rd.rdarray(dem, no_data=np.nan)
    rd_output = rd.ResolveFlats(rd_input)

    dem[:] = rd_output[:]
    dem.write(_output, overwrite=gscript.overwrite())


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
