#!/usr/bin/env python
############################################################################
#
# MODULE:     v.surf.nnbathy.py
#
# AUTHOR(S):  Adam Laza (mentor: Martin Landa)
#             (based on v.surf.nnbathy from GRASS 6)
#
# PURPOSE:    Interpolate raster surface using the "nnbathy" natural
#             neighbor interpolation program.
#
# COPYRIGHT:  (c) 2014 Adam Laza, and the GRASS Development Team
#
# LICENSE:    This program is free software under the GNU General Public
#             License (>=v2). Read the file COPYING that comes with
#             GRASS for details.
#
#############################################################################
#
# NOTES:
#
# 1. Requires nnbathy executable v 1.75 or later. Follow the instruction in
#    html manual page to obtain it.
#
# 2. When creating the input raster map, make sure it's extents cover
#    your whole region of interest, the cells you wish to interplate on are
#    NULL, and the resolution is correct. Same as most GRASS raster modules
#    this one is region sensitive too.

#%Module
#% description: Interpolates a raster map using the nnbathy natural neighbor interpolation program.
#% keywords: vector
#% keywords: surface
#% keywords: interpolation
#% keywords: natural
#% keywords: neighbor
#%end
#%option G_OPT_R_INPUT
#% key: input
#% type: string
#% description: Name of input raster map
#% guisection: Input data
#% required : yes
#%end
#%option G_OPT_R_OUTPUT
#% key: output
#% description: Name of output raster map
#%end
#%option
#% key: algorithm
#% type: string
#% options: l,nn,ns
#% answer: nn
#% descriptions: l;Linear;nn;Sibson natural neighbor;ns;Non-Sibsonian natural neighbor
#% description: Settings
#%end

import os
import sys

from grass.script.core import parser
import grass.script as grass

from nnbathy import Nnbathy_raster


def main():
    obj = Nnbathy_raster(options)
    obj.compute()
    obj.create_output()

if __name__ == "__main__":
    options, flags = parser()
    main()
