#!/usr/bin/env python
# -*- coding: utf-8 -*-

##############################################################################
#
# MODULE:       r.random.weight
# AUTHOR(S):    paulo van Breugel <paulo  ecodiv earth>
# PURPOSE:      Create a layer with weighted random sample
# COPYRIGHT: (C) 2014-2019 Paulo van Breugel and GRASS DEVELOPMENT TEAM
#            http://ecodiv.earth
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
import atexit
import grass.script as gs

CLEAN_RAST = []

def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all",
                       name=rast, quiet=True)


# Create temporary name
def tmpname(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = name + "_" + str(uuid.uuid4())
    tmpf = string.replace(tmpf, '-', '_')
    CLEAN_RAST.append(tmpf)
    return tmpf


# main function
def main(options, flags):

    # check if GISBASE is set
    if "GISBASE" not in os.environ:
        gs.fatal("You must be in GRASS GIS to run this program")

    # input raster map and parameters
    minval = options['start']
    maxval = options['end']
    weight = options['weights']
    outmap = options['output']
    subsample = options['subsample']
    seed = options['seed']
    flag_n = flags['n']

    # Compute minimum and maximum value raster
    minmax = gs.parse_command('r.univar', map=weight, flags='g', quiet=True)

    # Set min and max if not set, and check set min/max against map min and max
    if minval == '':
        minval = minmax['min']
    if maxval == '':
        maxval = minmax['max']
    if minval > minmax['min'] or maxval < minmax['max']:
        ms = ("\nYou defined the minimum and maximum weights\nas "
        + minval + " and " + maxval +
        " respectively. Note that the\nvalue range of weight raster is "
        + minmax['min'] + " - " + minmax['max'] + ".\nContinuing...\n\n")
        gs.message(ms)

    # setup temporary files and seed
    tmp_map1 = tmpname('r_w_rand1')
    tmp_map2 = tmpname('r_w_rand2')

    if seed == "auto":
        gs.mapcalc("$tmp_map1 = rand(float(${minval}),float(${maxval}))",
                   seed='auto', minval=minval, maxval=maxval,
                   tmp_map1=tmp_map1, quiet=True)
    else:
        gs.mapcalc("$tmp_map1 = rand(float(${minval}),float(${maxval}))",
                   seed=int(seed), minval=minval, maxval=maxval,
                   tmp_map1=tmp_map1, quiet=True)
    if flag_n:
        gs.mapcalc("${outmap} = if($tmp_map1 <= ${weight},1,0)",
                   weight=weight, outmap=tmp_map2, tmp_map1=tmp_map1,
                   quiet=True)
    else:
        gs.mapcalc("${outmap} = if($tmp_map1 <= ${weight},1,null())",
                   weight=weight, outmap=tmp_map2, tmp_map1=tmp_map1,
                   quiet=True)

    if subsample == '':
        gs.run_command("g.copy", raster=[tmp_map2, outmap], quiet=True)
    else:
        gs.run_command('r.null', map=tmp_map2, setnull=0, quiet=True)
        gs.run_command('r.random', input=tmp_map2, n=subsample, raster=outmap,
                       quiet=True)
        if flag_n:
            gs.run_command('r.null', map=outmap, null=0, quiet=True)

    # Add history
    if flag_n:
        nflag = "\n\t-n"
    else:
        nflag = ""
    desctxt = ("\n\nr.random.weight \n    weight={} \n    output={}"
               "    start={} \n    end={} \n    subsample={}"
               "\n    seed={}{}\n").format(weight, outmap, minval, maxval,
                                           subsample, seed, nflag)
    if flag_n:
        bso = "selected: 1/0"
    else:
        bso = "1 (selected)"
    gs.run_command("r.support", map=outmap, title="Weighted random sample",
                   units=bso, source1="", source2="",
                   description="Random sample points",
                   history=desctxt)

    gs.message("\n")
    gs.message("Ready!")
    gs.message("The name of the output raster is " + outmap + "\n")
    gs.message("\n")

if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
