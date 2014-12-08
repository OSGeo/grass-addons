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
#%option G_OPT_V_INPUT
#% key: input
#% type: string
#% description: Name of input vector points map
#% guisection: Input data
#% required : no
#%end
#%option G_OPT_V_FIELD
#% key: layer
#% label: Layer number
#% description: If set to 0, z coordinates are used. (3D vector only)
#% guisection: Selection
#%end
#%option G_OPT_F_INPUT
#% key: file
#% description: Containing x,y,z data as three space separated columns
#% guisection: Input data
#% required : no
#%end
#%option G_OPT_R_OUTPUT
#% key: output
#% description: Name of output raster map
#%end
#%option G_OPT_DB_COLUMN
#% key: zcolumn
#% description: Name of the attribute column with values to be used for approximation (if layer>0)
#% guisection: Settings
#%end
#%option G_OPT_DB_WHERE
#% key: kwhere
#% type: string
#% label: WHERE conditions of SQL query statement without 'where' keyword
#% guisection: Selection
#%end
#%option
#% key: algorithm
#% type: string
#% options: l,nn,ns
#% answer: nn
#% descriptions: l;Linear;nn;Sibson natural neighbor;ns;Non-Sibsonian natural neighbor
#% description: Settings
#%end

import sys
import os

from grass.script.core import parser
import grass.script as grass

from nnbathy import Nnbathy_vector, Nnbathy_file


def main():
    # initial controls
    if (options['input'] and options['file']):
        grass.fatal("Please specify either the 'input' \
                    or 'file' option, not both.")

    if not(options['input'] or options['file']):
        grass.message("Please specify either the 'input' or 'file' option.")

    if (options['file'] and os.path.isfile(options['file'])):
        grass.message("File "+options['file']+" does not exist.")

    # vector or file input?
    if (options['input']):
        obj = Nnbathy_vector(options)
    else:
        obj = Nnbathy_file(options)

    obj.compute()
    obj.create_output()

if __name__ == "__main__":
    options, flags = parser()
    main()
