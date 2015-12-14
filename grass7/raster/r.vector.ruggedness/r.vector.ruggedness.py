#!/usr/bin/env python
#
##############################################################################
#
# MODULE:       Vector Ruggedness Measure
#
# AUTHOR(S):    Adaption of original Sappington et al. (2007) script
#               by Steven Pawley
#
# PURPOSE:      This tool measures terrain ruggedness by calculating the vector
#               ruggedness measure described in Sappington, J.M., K.M. Longshore,
#               and D.B. Thomson. 2007. Quantifiying Landscape Ruggedness for
#               Animal Habitat Anaysis: A case Study Using Bighorn Sheep in
#               the Mojave Desert.
#               Journal of Wildlife Management. 71(5): 1419 -1426.
#
# COPYRIGHT:    (C) 2015 Steven Pawley, and by the GRASS Development Team
#
# DATE:         21 April 2015
#
##############################################################################

#%module
#% description: Vector Ruggedness Measure
#%end

import grass.script as grass
import random
import string
import atexit

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

tmp_rast = []

def cleanup():
    for rast in tmp_rast:
        grass.run_command("g.remove", name = rast, type = 'raster', flags = 'fb', quiet = True)

def main():
    # User specified variables
    dem = options['elevation']
    neighborhood_size = options['size']
    OutRaster = options['output']

    # Internal raster map names
    SlopeRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    AspectRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    xyRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    zRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    xRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    yRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    xSumRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    ySumRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    zSumRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])
    ResultRaster = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in xrange(8)])

    tmp_rast.append(SlopeRaster)
    tmp_rast.append(AspectRaster)
    tmp_rast.append(xyRaster)
    tmp_rast.append(zRaster)
    tmp_rast.append(xRaster)
    tmp_rast.append(yRaster)
    tmp_rast.append(xSumRaster)
    tmp_rast.append(ySumRaster)
    tmp_rast.append(zSumRaster)
    tmp_rast.append(ResultRaster)

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
    grass.message("Calculating x, y, and z rasters...")
    grass.mapcalc('{x} = sin({a})'.format(x=xyRaster, a=SlopeRaster))
    grass.mapcalc('{x} = cos({a})'.format(x=zRaster, a=SlopeRaster))
    grass.mapcalc('{x} = sin({a}) * {b}'.format(x=xRaster, a=AspectRaster, b=xyRaster))
    grass.mapcalc('{x} = cos({a}) * {b}'.format(x=yRaster, a=AspectRaster, b=xyRaster))

    # Calculate sums of x, y, and z rasters for selected neighborhood size
    grass.message("Calculating sums of x, y, and z rasters in selected neighborhood...")
    grass.run_command("r.neighbors", input = xRaster, output = xSumRaster, method = "average", size = neighborhood_size)
    grass.run_command("r.neighbors", input = yRaster, output = ySumRaster, method = "average", size = neighborhood_size)
    grass.run_command("r.neighbors", input = zRaster, output = zSumRaster, method = "average", size = neighborhood_size)

    # Calculate the resultant vector
    # Modified from the original script to multiple each SumRaster by the n neighborhood cells to get the sum
    grass.message("Calculating the resultant vector...")
    maxValue = int(neighborhood_size) * int(neighborhood_size)
    grass.mapcalc('{x} = sqrt(({a}*{d})^2 + ({b}*{d})^2 + ({c}*{d})^2)'.format(x=ResultRaster, a=xSumRaster, b=ySumRaster, c=zSumRaster, d=maxValue))

    # Calculate the Ruggedness raster
    grass.message("Calculating the final ruggedness raster...")
    grass.mapcalc('{x} = 1-({a} / {b})'.format(x=OutRaster, a=ResultRaster, b=maxValue))

    # Set the default color table
    grass.run_command("r.colors", flags = 'e', map = OutRaster, color = "ryb")

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    main()
