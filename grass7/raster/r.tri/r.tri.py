#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Terrain Ruggedness Index
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Calculates the Terrain Ruggedness Index (TRI) of
#                           Riley et al. (1999)
#
# COPYRIGHT:    (C) 2015 Steven Pawley, and by the GRASS Development Team
#
##############################################################################

#%module
#% description: Terrain Ruggedness Index
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster
#% key: dem
#% required : yes
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Terrain Ruggedness Index (TRI)
#% key: tri
#% required : yes
#%end

#%option
#% key: wsize
#% type: integer
#% description: Radius of neighbourhood in cells
#% answer: 1
#% guisection: Required
#%end

import sys
import os
import grass.script as grass

def main():
    dem = options['dem']
    tri = options['tri']
    wsize = int(options['wsize'])
    neighcells = ((wsize*2+1)**2)-1

    # calculate TRI based on map calc statements
    grass.message("Calculating the Topographic Ruggedness Index:")

    # generate a list of spatial neighbourhood indexs for the chosen radius
    # ignoring the center cell
    offsets = []
    for j in range(-wsize, wsize+1):
        for i in range(-wsize, wsize+1):
            if (j,i) != (0,0):
                offsets.append((j,i))

    # define the calculation term
    terms = ["abs($dem - $dem[%d,%d])" % d for d in offsets]

    # define the calculation expression
    expr = "$tri = (%s" % " + ".join(terms) + ") / $neighcells"

    # perform the r.mapcalc calculation with the moving window
    grass.mapcalc(expr, tri=tri, dem=dem, neighcells=neighcells)
    
    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
