#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       r.rand.weight
# AUTHOR(S):    paulo van Breugel <paulo at ecodiv.org>         
# PURPOSE:      Create a layer with weighted random sample
# COPYRIGHT: (C) 2014 Paulo van Breugel
#            http://ecodiv.org
#            http://pvanb.wordpress.com/
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

#%module
#% description: Weighted sample
#% keywords: raster, sample
#%end

#%option
#% key: weights
#% type: string
#% gisprompt: old,cell,raster
#% description: layer with weight
#% key_desc: raster
#% required: yes
#% multiple: no
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: output layer
#% key_desc: raster
#% required: yes
#% multiple: no
#%end

#%option
#% key: start
#% type: double
#% description: minimum weight
#% required: yes
#%end

#%option
#% key: end
#% type: double
#% description: maximum weight
#% required: yes
#%end

#%option
#% key: subsample
#% type: string
#% description: subsample
#% required: no
#% guisection: Sample options
#%end

#%option
#% key: seed
#% type: string
#% description: set seed for random number generation
#% answer: auto
#% required: no
#% guisection: Sample options
#%end

# import libraries
import os
import sys
import atexit
import time
import grass.script as grass

# Runs modules silently
#os.environ['GRASS_VERBOSE']='-1' 

def cleanup():
	grass.run_command('g.remove', 
      type = 'raster', 
      name = 'tmp_map',
      flags = 'f',
      quiet = True)

# main function
def main():
    global tmp_map
    
    # check if GISBASE is set
    if "GISBASE" not in os.environ:
    # return an error advice
       grass.fatal(_("You must be in GRASS GIS to run this program"))
       
    # input raster map and parameters   
    minval = options['start']
    maxval = options['end']
    weight = options['weights']
    outmap = options['output']
    subsample = options['subsample']
    seed = options['seed']
       
    # setup temporary files and seed
    tmp_map = 'r_w_rand_987654321'
    tmp_map2 = 'r_w_rand_987654321a'
    
    # Compute minimum and maximum value raster
    minmax = grass.parse_command('r.univar', 
        map = weight,
        flags='g')
   
    if seed == "auto":  
        grass.mapcalc("$tmp_map = rand(float(${minval}),float(${maxval}))", 
            seed='auto',
            minval = minval, 
            maxval = maxval,
            tmp_map = tmp_map)
    else:        
        grass.mapcalc("$tmp_map = rand(float(${minval}),float(${maxval}))", 
            seed=1,
            minval = minval, 
            maxval = maxval,
            tmp_map = tmp_map)

    grass.mapcalc("${outmap} = if($tmp_map <= ${weight},1,0)",
        weight = weight,
        outmap = outmap,
        tmp_map = tmp_map)
        
    if not subsample == '': 
        grass.run_command('r.null',
            map = outmap, 
            setnull = 0)
        grass.run_command('r.random',
            input = outmap,
            n = subsample,
            raster_output = outmap,
            overwrite=True)
        grass.run_command('r.null',
            map = outmap, 
            null = 0)

    print("------------------")
    print("Ready!")
    print("The name of raster created is " + outmap)
    if minval > minmax['min'] or maxval < minmax['max']:
        print("Warning!")
        print("You defined the minimum and maximum weights as: " + minval + " & " + maxval)
        print("Value range of weight raster is: " + minmax['min'] + " - " + minmax['max'])
    print("------------------")    

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())

