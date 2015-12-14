#! /usr/bin/env python
##############################################################################
#
# MODULE:       Pit and peak density
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Calculates the density of pits and peaks in a DEM
#                           Based on the methodology of Iwahashi & Pike (2007)
#                           Automated classifications of topography from DEMs by an unsupervised
#                           nested-means algorithm and a three-part geometric signature.
#                           Geomorphology. 86, 409-440
#
# COPYRIGHT:    (C) 2015 Steven Pawley, and by the GRASS Development Team
#
##############################################################################

#%module
#% description: Pit and peak density
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster:
#% key: elevation
#% required : yes
#%end

#%option
#% key: thres
#% type: double
#% description: Height threshold for pit and peak detection:
#% answer: 1
#% required: yes
#%end

#%option
#% key: window
#% type: double
#% description: Size of counting window:
#% answer: 21
#% guisection: Optional
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Texture Image:
#% key: pitdensity
#% required : yes
#%end

import sys
import random
import string
import grass.script as grass

def main():
    elevation = options['elevation']
    thres = options['thres']
    window = options['window']
    pitdensity = options['pitdensity']

    # Internal grid calculations - to be removed at end of process
    median = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    pitpeaks = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    pitcount = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])
    pitdensity_tmp = 'tmp_' + ''.join([random.choice(string.ascii_letters + string.digits) for n in range(8)])

    # Smooth the DEM
    grass.message("Smooth DEM with a 3x3 median filter:")
    grass.run_command("r.neighbors", input = elevation, method = "median", size = 3, output = median)

    # Extract the pits and peaks based on the threshold
    grass.message("Extract pits and peaks:")
    grass.mapcalc('{x} = if ( abs({dem}-{median})>{thres}, 1, null())'.format(x=pitpeaks, dem=elevation, thres=thres, median=median))

    # Count the number of pits and peaks
    grass.message("Count the number of pits and peaks in a moving window:")
    grass.run_command("r.neighbors", input = pitpeaks, method = "count", size = window, output = pitcount, flags = 'c')

    # Convert the pit and peak counts into a percentage
    grass.message("Convert the pit and peak counts into a percentage:")
    size = int(window)*int(window)
    grass.mapcalc('{x} = 100*{pitcount}/float({size})'.format(x=pitdensity_tmp, pitcount=pitcount, size = size))
 
    # Mask the raster to remove the background
    grass.message("Mask the terrain surface texture with the input DEM:")
    grass.run_command("r.mask", raster = elevation, maskcats = "*", layer = "1")
    grass.mapcalc('{x} = {pitdensity_tmp}'.format(x=pitdensity, pitdensity_tmp=pitdensity_tmp))
    grass.run_command("r.mask", raster = elevation, maskcats = "*", layer = "1", flags = 'r')

    # Clean-up
    grass.message("Deleting intermediate files:")
    grass.run_command("g.remove", type="raster", name=median, flags="f", quiet=True)
    grass.run_command("g.remove", type="raster", name=pitpeaks, flags="f", quiet=True)
    grass.run_command("g.remove", type="raster", name=pitcount, flags="f", quiet=True)
    grass.run_command("g.remove", type="raster", name=pitdensity_tmp, flags="f", quiet=True)

    return 0

if __name__ == "__main__":
    options, flags = grass.parser()
    sys.exit(main())
