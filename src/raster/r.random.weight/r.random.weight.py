#!/usr/bin/env python

##############################################################################
#
# MODULE:       r.random.weight
# AUTHOR(S):    paulo van Breugel <paulo  ecodiv earth>
# PURPOSE:      Create a layer with weighted random sample
# COPYRIGHT: (C) 2014-2022 Paulo van Breugel and GRASS DEVELOPMENT TEAM
#            https://ecodiv.earth
#
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
##############################################################################

# %module
# % description: Generates a binary raster layer with a random selection of raster cells depending on the weight of each cell in the input weight layer.
# % keyword: raster
# % keyword: sampling
# % keyword: random
# %end

# %option
# % key: weights
# % type: string
# % gisprompt: old,cell,raster
# % description: layer with weight
# % key_desc: raster
# % required: yes
# % multiple: no
# %end

# %option
# % key: output
# % type: string
# % gisprompt: new,cell,raster
# % description: output layer
# % key_desc: raster
# % required: yes
# % multiple: no
# %end

# %option
# % key: start
# % type: double
# % description: minimum weight
# % required: no
# % guisection: Sample options
# %end

# %option
# % key: end
# % type: double
# % description: maximum weight
# % required: no
# % guisection: Sample options
# %end

# %option
# % key: subsample
# % type: string
# % description: subsample
# % required: no
# % guisection: Sample options
# %end

# %option
# % key: seed
# % type: integer
# % description: set seed for random number generation
# % required: no
# % guisection: Sample options
# %end

# %flag
# % key: s
# % description: Generate random seed (result is non-deterministic)
# % guisection: Sample options
# %end

# %rules
# %exclusive: -s,seed
# %end

# %flag
# % key: n
# % description: set non-selected values to 0 (default to NULL)
# %end


# import libraries
import os
import sys
import uuid
import atexit
import grass.script as gs

CLEAN_RAST = []


def cleanup():
    """Remove temporary maps specified in the global list"""
    cleanrast = list(reversed(CLEAN_RAST))
    for rast in cleanrast:
        gs.run_command("g.remove", flags="f", type="all", name=rast, quiet=True)


# Create temporary name
def tmpname(name):
    """Generate a tmp name which contains prefix
    Store the name in the global list.
    Use only for raster maps.
    """
    tmpf = "{}_{}".format(name, str(uuid.uuid4()))
    tmpf = tmpf.replace("-", "_")
    CLEAN_RAST.append(tmpf)
    return tmpf


# main function
def main(options, flags):

    # check if GISBASE is set
    if "GISBASE" not in os.environ:
        gs.fatal("You must be in GRASS GIS to run this program")

    # input raster map and parameters
    minval = options["start"]
    maxval = options["end"]
    weight = options["weights"]
    outmap = options["output"]
    subsample = options["subsample"]
    seed = options["seed"]
    flag_n = flags["n"]
    flag_seed = flags["s"]

    # Compute minimum and maximum value raster
    minmax = gs.parse_command("r.univar", map=weight, flags="g", quiet=True)

    # Set min and max if not set, and check set min/max against map min and max
    if minval == "":
        minval = minmax["min"]
    if maxval == "":
        maxval = minmax["max"]
    if minval > minmax["min"] or maxval < minmax["max"]:
        ms = (
            "\nYou defined the minimum and maximum weights\nas {} and {} "
            "respectively. Note that the\nvalue range of weight raster is"
            " {} - {}.\nContinuing ...\n\n".format(
                minval, maxval, minmax["min"], minmax["max"]
            )
        )
        gs.message(ms)

    # setup temporary files and seed
    tmp_map1 = tmpname("r_w_rand1")
    tmp_map2 = tmpname("r_w_rand2")

    if flag_seed:
        gs.mapcalc(
            "$tmp_map1 = rand(float(${minval}),float(${maxval}))",
            seed="auto",
            minval=minval,
            maxval=maxval,
            tmp_map1=tmp_map1,
            quiet=True,
        )
    else:
        gs.mapcalc(
            "$tmp_map1 = rand(float(${minval}),float(${maxval}))",
            seed=int(seed),
            minval=minval,
            maxval=maxval,
            tmp_map1=tmp_map1,
            quiet=True,
        )
    if flag_n:
        gs.mapcalc(
            "${outmap} = if($tmp_map1 <= ${weight},1,0)",
            weight=weight,
            outmap=tmp_map2,
            tmp_map1=tmp_map1,
            quiet=True,
        )
    else:
        gs.mapcalc(
            "${outmap} = if($tmp_map1 <= ${weight},1,null())",
            weight=weight,
            outmap=tmp_map2,
            tmp_map1=tmp_map1,
            quiet=True,
        )

    if subsample == "":
        gs.run_command("g.copy", raster=[tmp_map2, outmap], quiet=True)
    else:
        gs.run_command("r.null", map=tmp_map2, setnull=0, quiet=True)
        if flag_seed:
            gs.run_command(
                "r.random",
                input=tmp_map2,
                n=subsample,
                raster=outmap,
                flags="s",
                quiet=True,
            )
        else:
            gs.run_command(
                "r.random",
                input=tmp_map2,
                n=subsample,
                raster=outmap,
                seed=seed,
                quiet=True,
            )
        if flag_n:
            gs.run_command("r.null", map=outmap, null=0, quiet=True)

    # Add history
    if flag_n:
        nflag = "\n\t-n"
    else:
        nflag = ""
    if flag_seed:
        seednumber = "random"
    else:
        seednumber = seed
    desctxt = (
        "\n\nr.random.weight \n    weight={} \n    output={}"
        "    start={} \n    end={} \n    subsample={}"
        "\n    seed={}{}\n"
    ).format(weight, outmap, minval, maxval, subsample, seednumber, nflag)
    if flag_n:
        bso = "selected: 1/0"
    else:
        bso = "1 (selected)"
    gs.run_command(
        "r.support",
        map=outmap,
        title="Weighted random sample",
        units=bso,
        source1="",
        source2="",
        description="Random sample points",
        history=desctxt,
    )

    gs.message("\n")
    gs.message("Ready!")
    gs.message("The name of the output raster is {}\n".format(outmap))
    gs.message("\n")


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main(*gs.parser()))
