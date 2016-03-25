#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       r.random.weight
# AUTHOR(S):    paulo van Breugel <paulo at ecodiv.org>
# PURPOSE:      Create a layer with weighted random sample
# COPYRIGHT: (C) 2014-2016 Paulo van Breugel
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
#% required: no
#% guisection: Sample options
#%end

#%option
#% key: end
#% type: double
#% description: maximum weight
#% required: no
#% guisection: Sample options
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
import tempfile
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
        grass.fatal("You must be in GRASS GIS to run this program")

    # input raster map and parameters
    minval = options['start']
    maxval = options['end']
    weight = options['weights']
    outmap = options['output']
    subsample = options['subsample']
    seed = options['seed']
    flag_n = flags['n']

    # Compute minimum and maximum value raster
    minmax = grass.parse_command('r.univar', map = weight,  flags='g', quiet=True)

    # Set min and max if not set, and check set minimum/maximum against map min and max
    if minval == '':
        minval = minmax['min']
    if maxval == '':
        maxval = minmax['max']
    if minval > minmax['min'] or maxval < minmax['max']:
        grass.message("\nYou defined the minimum and maximum weights\nas "
        + minval + " and " + maxval + " respectively. Note that the\nvalue range of weight raster is "
        + minmax['min'] + " - " + minmax['max'] +".\nContinuing...\n\n")

    # setup temporary files and seed
    tmp_map1 = tmpname('r_w_rand1')
    tmp_map2 = tmpname('r_w_rand2')

    if seed == "auto":
        grass.mapcalc("$tmp_map1 = rand(float(${minval}),float(${maxval}))",
            seed='auto',
            minval = minval,
            maxval = maxval,
            tmp_map1 = tmp_map1, quiet=True)
    else:
        grass.mapcalc("$tmp_map1 = rand(float(${minval}),float(${maxval}))",
            seed=int(seed),
            minval = minval,
            maxval = maxval,
            tmp_map1 = tmp_map1, quiet=True)
    if flag_n:
        grass.mapcalc("${outmap} = if($tmp_map1 <= ${weight},1,0)",
            weight = weight,
            outmap = tmp_map2,
            tmp_map1 = tmp_map1, quiet=True)
    else:
        grass.mapcalc("${outmap} = if($tmp_map1 <= ${weight},1,null())",
            weight = weight,
            outmap = tmp_map2,
            tmp_map1 = tmp_map1, quiet=True)

    if subsample == '':
        grass.run_command("g.copy", raster=[tmp_map2, outmap], quiet=True)
    else:
        grass.run_command('r.null',
            map = tmp_map2,
            setnull = 0, quiet=True)
        grass.run_command('r.random',
            input = tmp_map2,
            n = subsample,
            raster = outmap,
            quiet=True)
        if flag_n:
            grass.run_command('r.null',
                map = outmap,
                null = 0, quiet=True)

    # Add history
    if flag_n:nflag="\n\t-n"
    else: nflag=""
    desctxt = "r.random.weight \n\tweight=" + weight + "\n\toutput=" + \
        outmap + "\n\tstart=" + str(minval) + "\n\tend=" + str(maxval) + \
        "\n\tsubsample=" + str(subsample) + "\n\tseed=" + str(seed) +  nflag

    fd8, tmphist = tempfile.mkstemp()
    text_file = open(tmphist, "w")
    text_file.write(desctxt + "\n\n")
    text_file.close()
    if flag_n:
        bso = "selected: 1/0"
    else:
        bso = "1 (selected)"

    grass.run_command("r.support", map=outmap,
                      title="Weighted random sample",
                      units=bso,
                      source1="",
                      source2="",
                      description="Random sample points",
                      loadhistory=tmphist)
    os.close(fd8)
    os.remove(tmphist)

    grass.message("------------------")
    grass.message("Ready!")
    grass.message("The name of raster created is " + outmap + "\n\n")

if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())

