#!/usr/bin/env python
############################################################################
#
# MODULE:       r.richdem.breachdepressions
#
# AUTHOR(S):    Richard Barnes, Andrew Wickert
#
# PURPOSE:      Breaches all depressions in a DEM.
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
# % description: Breaches depressions using RichDEM
# % keyword: raster
# % keyword: hydrology
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  label: Input DEM
# %  required: yes
# %end

# %option
# % key: topology
# % type: string
# % label: D4 or D8 flow routing?
# % required: no
# % multiple: no
# % answer: D8
# % options: D4,D8
# %end

# %option G_OPT_R_OUTPUT
# %  key: output
# %  label: Output DEM with depressions breached
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
    RichDEM depression breaching
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
    _topology = options["topology"]

    dem = garray.array(_input, null=np.nan)

    rd_inout = rd.rdarray(dem, no_data=np.nan)
    rd.BreachDepressions(dem=rd_inout, in_place=True, topology=_topology)

    dem[:] = rd_inout[:]
    dem.write(_output, overwrite=gscript.overwrite())


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
