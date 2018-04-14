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
#% key: p
#% label: Cell padding
#% description: Use cell padding to reduce edge effect
#% guisection: Optional
#%end


import sys
import atexit
import random
import string
import grass.script as gs
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.gis.region import Region
from grass.pygrass.raster import RasterRow

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


def main():
    dem = options['input']
    tri = options['output']
    size = int(options['size'])
    p = flags['p']

    radius = (size-1)/2
    ncells = size**2

    # store current region settings
    current_reg = Region()

    if p:
        # check for existing mask
        if RasterRow('MASK').exist():
            gs.fatal('Cell padding option cannot be used with existing mask...please remove first')

        # grow the map to remove border effects
        gs.message('Growing DEM to avoid edge effects...')
        dem_grown = temp_map('tmp_elevation_grown')
        g.region(n=current_reg.north + (current_reg.nsres * (radius+2)),
                 s=current_reg.south - (current_reg.nsres * (radius+2)),
                 w=current_reg.west - (current_reg.ewres * (radius+2)),
                 e=current_reg.east + (current_reg.ewres * (radius+2)))
        r.grow(input=dem, output=dem_grown, radius=radius+2, quiet=True)
        dem = dem_grown

    # calculate TRI based on map calc statements
    gs.message("Calculating the Topographic Ruggedness Index...")

    # generate a list of spatial neighbourhood indexs for the chosen radius
    # ignoring the center cell
    offsets = []
    for j in range(-radius, radius+1):
        for i in range(-radius, radius+1):
            if (j,i) != (0,0):
                offsets.append((j,i))

    # define the calculation term
    terms = ["($dem - $dem[%d,%d])^2" % d for d in offsets]

    # define the calculation expression
    expr = "$tri = sqrt((%s" % " + ".join(terms) + ") / $ncells)"

    # perform the r.mapcalc calculation with the moving window
    if p:
        output_tmp = temp_map('tmp')
        gs.mapcalc(expr, tri=output_tmp, dem=dem, ncells=ncells)
        r.mask(raster=options['input'], quiet=True)
        r.mapcalc('{x}={y}'.format(x=tri, y=output_tmp))
        r.mask(flags='r', quiet=True)
        Region.write(current_reg)
    else:
        gs.mapcalc(expr, tri=tri, dem=dem, ncells=ncells)

    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
