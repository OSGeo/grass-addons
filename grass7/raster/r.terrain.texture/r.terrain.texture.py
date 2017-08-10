#! /usr/bin/env python
##############################################################################
#
# MODULE:       Pit and peak density
#
# AUTHOR(S):    Steven Pawley
#
# PURPOSE:      Calculates the density of pits and peaks in a DEM
#               Based on the methodology of Iwahashi & Pike (2007)
#               Automated classifications of topography from DEMs by an unsupervised
#               nested-means algorithm and a three-part geometric signature.
#               Geomorphology. 86, 409-440
#
# COPYRIGHT:    (C) 2017 Steven Pawley and by the GRASS Development Team
#
##############################################################################

#%module
#% description: Pit and peak density
#% keyword: raster
#% keyword: terrain 
#% keyword: classification
#%end

#%option G_OPT_R_INPUT
#% description: Input elevation raster:
#% key: input
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
#% key: size
#% type: double
#% description: Size of counting window:
#% answer: 21
#% guisection: Optional
#%end

#%option G_OPT_R_OUTPUT
#% description: Output Texture Image:
#% key: output
#% required : yes
#%end

import sys
import random
import string
from subprocess import PIPE
import atexit
import grass.script as gs
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.script.utils import parse_key_val

TMP_RAST = []

def cleanup():
    gs.message("Deleting intermediate files...")
    
    for f in TMP_RAST:
        gs.run_command(
            "g.remove", type="raster", name=f, flags="f", quiet=True)

def main():
    elevation = options['input']
    thres = float(options['thres'])
    window = int(options['size'])
    pitdensity = options['output']

    # current region settings
    current_reg = parse_key_val(
        g.region(flags='pg', stdout_=PIPE).outputs.stdout)
    del current_reg['projection']
    del current_reg['zone']
    del current_reg['cells']

    # Smooth the DEM
    gs.message("Smoothing input DEM with a 3x3 median filter...")
    filtered_dem = 'tmp_filtred_dem' + ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST.append(filtered_dem)
    
    gs.run_command("r.neighbors", input = elevation, method = "median",
                   size = 3, output = filtered_dem, flags='c', quiet=True)
            
    # Extract the pits and peaks based on the threshold
    pitpeaks = 'tmp_pitpeaks' + ''.join(
        [random.choice(string.ascii_letters + string.digits) for n in range(4)])
    TMP_RAST.append(pitpeaks)

    gs.message("Extracting pits and peaks with difference > thres...")
    gs.mapcalc(
        '{x} = if ( abs({dem}-{median})>{thres}, 1, 0)'.format(
                x=pitpeaks, dem=elevation, thres=thres, median=filtered_dem),
                quiet=True)
    
    # calculate density of pits and peaks
    gs.message("Using resampling filter to create terrain texture...")
    window_radius = (window-1)/2
    y_radius = float(current_reg['ewres'])*window_radius
    x_radius = float(current_reg['nsres'])*window_radius
    
    r.resamp_filter(input=pitpeaks, output=pitdensity, filter=['bartlett','gauss'],
                    radius=[x_radius,y_radius])
    
    # return to original region
    g.region(**current_reg)

    # set colors
    r.colors(map=pitdensity, color='haxby', quiet=True)
 
    return 0

if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
