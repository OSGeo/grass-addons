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
#% key_desc: weight
#% required: yes
#% multiple: no
#%end

#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: output layer
#% key_desc: output
#% required: yes
#% multiple: no
#%end

#%option
#% key: start
#% type: double
#% description: minimum weight
#% key_desc: start
#% answer: 0
#% required: yes
#%end

#%option
#% key: end
#% type: double
#% description: maximum weight
#% key_desc: end
#% answer: 100
#% required: yes
#%end

#%option
#% key: subsample
#% type: string
#% description: subsample - not implemented yet
#% key_desc: ss
#% answer: 0
#% required: no
#%end

#%option
#% key: seed
#% type: double
#% description: set seed for random number generation
#% key_desc: seed
#% required: no
#%end

# import libraries
import os
import sys
import atexit
import time
import grass.script as grass

# Runs modules silently
# os.environ['GRASS_VERBOSE']='-1' 

def cleanup():
	grass.run_command('g.remove', flags = 'f',
      type = 'raster', name = tmp_map, quiet = True)

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
    if seed == "":
        ticks = str(int(time.time()*1000)),
        print("seed used is: " + str(ticks[0]))
        os.environ['GRASS_RND_SEED'] = ticks[0]
    else:
        print("Seed used for random number generation is: " + str(seed))
        
    grass.mapcalc("$tmp_map = rand(${minval},${maxval})", 
        minval = minval, 
        maxval = maxval,
        tmp_map = tmp_map)
   
    grass.mapcalc("${outmap} = if($tmp_map < ${weight},1,0)",
        weight = weight,
        outmap = outmap,
        tmp_map = tmp_map)
    
    print("Ready, name of raster created is " + outmap)
    
if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())

