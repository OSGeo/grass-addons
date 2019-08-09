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

#%flag
#% key: c
#% description: Use circular neighborhood
#%end

from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.gis.region import Region
from grass.pygrass.raster import RasterRow
import sys
import atexit
import random
import string
import grass.script as gs

TMP_RAST = []

def cleanup():
    gs.message("Deleting intermediate files...")

    for f in TMP_RAST:
        gs.run_command(
            "g.remove", type="raster", name=f, flags="f", quiet=True)


def temp_map(name):
    tmp = name + ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST.append(tmp)

    return (tmp)


def focal_expr(radius, window_square=False):
    """Returns array offsets relative to centre pixel (0,0) for a matrix of
    size radius

    Args
    ----
    radius : int
        Radius of the focal function
    window_square : bool. Optional (default is False)
        Boolean to use a circular or square window

    Returns
    -------
    offsets : list
        List of pixel positions (row, col) relative to the center pixel
        ( 1, -1)  ( 1, 0)  ( 1, 1)
        ( 0, -1)  ( 0, 0)  ( 0, 1)
        (-1, -1)  (-1, 0)  (-1, 1)"""

    offsets = []

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the centre cell
    if window_square:
        
        for i in range(-radius, radius+1):
            for j in range(-radius, radius+1):
                if (i,j) != (0,0):
                    offsets.append((i, j))
    
    else:

        for i in range(-radius, radius+1):
            for j in range(-radius, radius+1):
                row = i + radius
                col = j + radius

                if pow(row - radius, 2) + pow(col - radius, 2) <= \
                    pow(radius, 2) and (i, j) != (0,0):
                    offsets.append((j, i))

    return offsets


def main():
    dem = options['input']
    tri = options['output']
    size = int(options['size'])
    circular = flags['c']

    radius = int((size-1)/2)

    # calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index...")

    # generate a list of spatial neighbourhood offsets for the chosen radius
    # ignoring the center cell
    offsets = focal_expr(radius = radius, window_square=not circular)
    terms = []
    for d in offsets:
        valid = ','.join(map(str, d))        
        invalid = ','.join([str(-d[0]), str(-d[1])])
        terms.append(
            "if(isnull({dem}[{d}]), if(isnull({dem}[{e}]), (median({dem})-{dem})^2, ({dem}[{e}]-{dem}^2)), ({dem}[{d}]-{dem})^2)".format(
            dem=dem, d=valid, e=invalid))

    # define the calculation expression
    ncells = len(offsets)+1
    expr = "$tri = sqrt((%s" % " + ".join(terms) + ") / $ncells)"

    # perform the r.mapcalc calculation with the moving window
    gs.mapcalc(expr, tri=tri, dem=dem, ncells=ncells)

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
