#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Vector Ruggedness Measure
#
# AUTHOR(S):   Adaption of original Sappington et al. (2007) script
#                       by Steven Pawley
#
# PURPOSE:     This tool measures terrain ruggedness by calculating the vector
#                       ruggedness measure described in Sappington, J.M., K.M. Longshore,
#                       and D.B. Thomson. 2007. Quantifiying Landscape Ruggedness for
#                       Animal Habitat Anaysis: A case Study Using Bighorn Sheep in
#                       the Mojave Desert.
#                       Journal of Wildlife Management. 71(5): 1419 -1426.
#
# COPYRIGHT: (C) 2016 Steven Pawley, and by the GRASS Development Team
#
# DATE:            30 June 2016
#
##############################################################################

#%module
#% description: Vector Ruggedness Measure
#%end

import grass.script as grass
import random
import string
import atexit
import copy
from grass.pygrass.modules import Module, ParallelModuleQueue

#%option G_OPT_R_INPUTS
#% key: elevation
#% label: DEM Raster Input
#%end

#%option
#% key: size
#% type: integer
#% description: Size of neighbourhood
#% answer: 3
#% guisection: Required
#%end

#%option G_OPT_R_OUTPUTS
#% key: output
#% label: Vector Ruggedness Index Output
#%end

#%flag
#% key: p
#% label: Do not run in parallel
#% guisection: Optional
#%end

tmp_rast = []

def cleanup():
    for rast in tmp_rast:
        grass.run_command("g.remove", name = rast, type = 'raster', flags = 'fb', quiet = True)

def main():
    # User specified variables
    dem = options['elevation']
    neighborhood_size = options['size']
    OutRaster = options['output']
    notparallel = flags['p']

    # Internal raster map names
    SlopeRaster = 'tmpSlope_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    AspectRaster = 'tmpAspect_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    xyRaster = 'tmpxyRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    zRaster = 'tmpzRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    xRaster = 'tmpxRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    yRaster = 'tmpyRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    xSumRaster = 'tmpxSumRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    ySumRaster = 'tmpySumRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    zSumRaster = 'tmpzSumRaster_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])

    tmp_rast.append(SlopeRaster)
    tmp_rast.append(AspectRaster)
    tmp_rast.append(xyRaster)
    tmp_rast.append(zRaster)
    tmp_rast.append(xRaster)
    tmp_rast.append(yRaster)
    tmp_rast.append(xSumRaster)
    tmp_rast.append(ySumRaster)
    tmp_rast.append(zSumRaster)

    # Create Slope and Aspect rasters
    grass.message("Calculating slope and aspect...")
    grass.run_command("r.slope.aspect",
                      elevation = dem,
                      slope = SlopeRaster,
                      aspect = AspectRaster,
                      format = "degrees",
                      precision = "FCELL",
                      zscale = 1.0,
                      min_slope = 0.0,
                      quiet = True)

    # Calculate x y and z rasters
    # Note - GRASS sin/cos functions differ from ArcGIS which expects input grid in radians, whereas GRASS functions expect degrees
    # No need to convert slope and aspect to radians as in the original ArcGIS script

    if notparallel == False:
        # parallel version
        grass.message("Calculating x, y, and z rasters...")

        # calculate xy and z rasters using two parallel processes
        mapcalc_list = []
        mapcalc = Module("r.mapcalc", run_=False)
        queue = ParallelModuleQueue(nprocs=2)

        mapcalc1 = copy.deepcopy(mapcalc)
        mapcalc_list.append(mapcalc1)
        m = mapcalc1(expression='{x} = float(sin({a}))'.format(x=xyRaster, a=SlopeRaster))
        queue.put(m)

        mapcalc2 = copy.deepcopy(mapcalc)
        mapcalc_list.append(mapcalc2)
        m = mapcalc2(expression='{x} = float(cos({a}))'.format(x=zRaster, a=SlopeRaster))
        queue.put(m)

        queue.wait()

        # calculate x and y rasters using two parallel processes
        mapcalc_list = []
        mapcalc = Module("r.mapcalc", run_=False)
        queue = ParallelModuleQueue(nprocs=2)

        mapcalc1 = copy.deepcopy(mapcalc)
        mapcalc_list.append(mapcalc1)
        m = mapcalc1(expression='{x} = float(sin({a}) * {b})'.format(x=xRaster, a=AspectRaster, b=xyRaster))
        queue.put(m)

        mapcalc2 = copy.deepcopy(mapcalc)
        mapcalc_list.append(mapcalc2)
        m = mapcalc2(expression='{x} = float(cos({a}) * {b})'.format(x=yRaster, a=AspectRaster, b=xyRaster))
        queue.put(m)

        queue.wait()
    else:
        grass.mapcalc('{x} = float(sin({a}))'.format(x=xyRaster, a=SlopeRaster))
        grass.mapcalc('{x} = float(cos({a}))'.format(x=zRaster, a=SlopeRaster))
        grass.mapcalc('{x} = float(sin({a}) * {b})'.format(x=xRaster, a=AspectRaster, b=xyRaster))
        grass.mapcalc('{x} = float(cos({a}) * {b})'.format(x=yRaster, a=AspectRaster, b=xyRaster))

    # Calculate sums of x, y, and z rasters for selected neighborhood size

    if notparallel == False:
        # parallel version using three parallel processes
        grass.message("Calculating sums of x, y, and z rasters in selected neighborhood...")

        n_list = []
        neighbors = Module("r.neighbors", overwrite=True, run_=False)
        queue = ParallelModuleQueue(nprocs=3)

        n1 = copy.deepcopy(neighbors)
        n_list.append(n1)
        n = n1(input = xRaster, output = xSumRaster, method = "average", size = neighborhood_size)
        queue.put(n1)

        n2 = copy.deepcopy(neighbors)
        n_list.append(n2)
        n = n2(input = yRaster, output = ySumRaster, method = "average", size = neighborhood_size)
        queue.put(n2)

        n3 = copy.deepcopy(neighbors)
        n_list.append(n3)
        n = n3(input = zRaster, output = zSumRaster, method = "average", size = neighborhood_size)
        queue.put(n3)

        queue.wait()
    else:
        grass.run_command("r.neighbors", input = xRaster, output = xSumRaster, method = "average", size = neighborhood_size)
        grass.run_command("r.neighbors", input = yRaster, output = ySumRaster, method = "average", size = neighborhood_size)
        grass.run_command("r.neighbors", input = zRaster, output = zSumRaster, method = "average", size = neighborhood_size)

    # Calculate the resultant vector and final ruggedness raster
    # Modified from the original script to multiple each SumRaster by the n neighborhood cells to get the sum
    grass.message("Calculating the final ruggedness raster...")
    maxValue = int(neighborhood_size) * int(neighborhood_size)
    grass.mapcalc('{x} = float(1-( (sqrt(({a}*{d})^2 + ({b}*{d})^2 + ({c}*{d})^2) / {e})))'.format(x=OutRaster, a=xSumRaster, b=ySumRaster, c=zSumRaster, d=maxValue, e=maxValue))

    # Set the default color table
    grass.run_command("r.colors", flags = 'e', map = OutRaster, color = "ryb")

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
