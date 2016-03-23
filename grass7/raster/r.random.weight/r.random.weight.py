#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       r.random.weight
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
#% description: Generates a binary raster layer with a random selection of raster cells depending on the weight of each cell in the input weight layer.
#% keyword: raster
#% keyword: sampling
#% keyword: random
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

#%flag
#% key: n
#% description: set non-selected values to 0 (default to NULL)
#%end


# import libraries
import os
import sys
import uuid
import string
import atexit
import grass.script as grass

clean_rast = set()
def cleanup():
    for rast in clean_rast:
        grass.run_command("g.remove", flags="f",
        type="rast", name = rast, quiet = True)

# Create temporary name
def tmpname(name):
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    clean_rast.add(tmpf)
    return tmpf

# main function
def main():

    # check if GISBASE is set
    if "GISBASE" not in os.environ:
        grass.fatal(_("You must be in GRASS GIS to run this program"))

    # input raster map and parameters
    minval = options['start']
    maxval = options['end']
    weight = options['weights']
    outmap = options['output']
    subsample = options['subsample']
    seed = options['seed']
    flag_n = flags['n']

    # Check set minimum/maximum against map min and max
    if minval > minmax['min'] or maxval < minmax['max']:
    grass.message("You defined the minimum and maximum weights as: "
        + minval + " & " + maxval + ". Value range of weight raster is: "
        + minmax['min'] + " - " + minmax['max'] +". Continuing...")

    # setup temporary files and seed
    tmp_map = tmpname('r_w_rand')

    # Compute minimum and maximum value raster
    minmax = grass.parse_command('r.univar',
        map = weight,
        flags='g', quiet=True)

    if seed == "auto":
        grass.mapcalc("$tmp_map = rand(float(${minval}),float(${maxval}))",
            seed='auto',
            minval = minval,
            maxval = maxval,
            tmp_map = tmp_map, quiet=True)
    else:
        grass.mapcalc("$tmp_map = rand(float(${minval}),float(${maxval}))",
            seed=int(seed),
            minval = minval,
            maxval = maxval,
            tmp_map = tmp_map, quiet=True)
    clean_rast.add(tmp_map)

    if flag_n:
        grass.mapcalc("${outmap} = if($tmp_map <= ${weight},1,0)",
            weight = weight,
            outmap = outmap,
            tmp_map = tmp_map, quiet=True)
    else:
        grass.mapcalc("${outmap} = if($tmp_map <= ${weight},1,null())",
            weight = weight,
            outmap = outmap,
            tmp_map = tmp_map, quiet=True)

    if not subsample == '':
        grass.run_command('r.null',
            map = outmap,
            setnull = 0, quiet=True)
        grass.run_command('r.random',
            input = outmap,
            n = subsample,
            raster_output = outmap,
            overwrite=True, quiet=True)
        if flag_n:
            grass.run_command('r.null',
                map = outmap,
                null = 0, quiet=True)

    grass.message("------------------")
    grass.message("Ready!")
    grass.message("The name of raster created is " + outmap)

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())

