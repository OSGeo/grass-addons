#!/usr/bin/env python
############################################################################
#
# MODULE:       r.richdem.terrainattribute
#
# AUTHOR(S):    Richard Barnes, Andrew Wickert
#
# PURPOSE:      Calculates a set of terrain attributes (slope, aspect, ...)
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
# % description: Calculates local terrain attributes.
# % keyword: raster
# %end

# %option G_OPT_R_INPUT
# %  key: input
# %  label: Input DEM
# %  required: yes
# %end

# %option
# % key: attribute
# % type: string
# % label: Terrain attribute to calculate.
# % required: yes
# % multiple: no
# % options: slope_riserun,slope_percentage,slope_degrees,slope_radians,aspect,curvature,planform_curvature,profile_curvature
# %end

# %option
# % key: zscale
# % type: double
# % label: Scalar multiplier for elevation (vertical exaggeration)
# % required: no
# % answer: 1.0
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
    _attribute = options["attribute"]
    _zscale = float(options["zscale"])

    dem = garray.array()
    dem.read(_input, null=np.nan)

    rd_input = rd.rdarray(dem, no_data=np.nan)
    del dem
    rd_output = rd.TerrainAttribute(dem=rd_input, attrib=_attribute, zscale=_zscale)

    outarray = garray.array()
    outarray[:] = rd_output[:]
    outarray.write(_output, overwrite=gscript.overwrite())


if __name__ == "__main__":
    options, flags = gscript.parser()
    main()
