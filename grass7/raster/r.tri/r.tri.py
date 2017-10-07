#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Terrain Ruggedness Index
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Simple script to calculate the Terrain Ruggedness Index (TRI)
#               of Riley et al. (1999)
#
# COPYRIGHT:    (C) 2015 Steven Pawley and by the GRASS Development Team
#
###############################################################################

#%module
#% description: Terrain Ruggedness Index
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster
#% key: input
#% required : yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Terrain Ruggedness Index (TRI)
#% key: output
#% required : yes
#%end

#%option
#% key: size
#% type: integer
#% description: Size of neighbourhood in cells
#% answer: 3
#% guisection: Required
#%end

import sys
import grass.script as gs

def main():
    dem = options['input']
    tri = options['output']
    size = int(options['size'])

    radius = (size-1)/2
    neighcells = (size**2)-1

    # calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index:")

    # generate a list of spatial neighbourhood indexs for the chosen radius
    # ignoring the center cell
    offsets = []
    for j in range(-radius, radius+1):
        for i in range(-radius, radius+1):
            if (j,i) != (0,0):
                offsets.append((j,i))

    # define the calculation term
    terms = ["abs($dem - $dem[%d,%d])" % d for d in offsets]

    # define the calculation expression
    expr = "$tri = float(%s" % " + ".join(terms) + ") / $neighcells"

    # perform the r.mapcalc calculation with the moving window
    gs.mapcalc(expr, tri=tri, dem=dem, neighcells=neighcells)

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
