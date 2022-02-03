#!/usr/bin/env python
#
############################################################################
#
# MODULE:		Set of time discrete population models in fisheries science
#
# AUTHOR(S):		Johannes Radinger
#
# VERSION:
#
# DATE:			2013-11-27
#
#############################################################################
# %Module
# % description: Set of population models (fisheries science)
# % keyword: Population growth model
# %End
# %option
# % key: n_initial
# % type: string
# % gisprompt: old,cell,raster
# % description: Map of number of individuals per cell at time t0 (initial population size)
# % required: yes
# %end
# %option
# % key: timesteps
# % type: integer
# % description: Number of time steps
# % required: yes
# % answer: 1
# %end
# %Option
# % key: exponential_output
# % type: string
# % gisprompt: new,cell,raster
# % required: no
# % multiple: no
# % key_desc: name
# % description: Name for exponential model output map
# % guisection: Exponential
# %end
# %option
# % key: r_exp_value
# % type: double
# % description: Cell-specific fixed value of intrinsic rate of increase, log(finite rate of increase, lambda)
# % required: no
# % multiple: no
# % guisection: Exponential
# %end
# %option
# % key: r_exp_map
# % type: string
# % gisprompt: old,cell,raster
# % description: Map of cell-specific intrinsic rate of increase, log(finite rate of increase, lambda)
# % required: no
# % multiple: no
# % guisection: Exponential
# %end
# %Option
# % key: ricker_output
# % type: string
# % gisprompt: new,cell,raster
# % required: no
# % multiple: no
# % key_desc: name
# % description: Name for Ricker model output map
# % guisection: Ricker
# %end
# %option
# % key: k_value
# % type: integer
# % description: Fixed value of carrying capacity of the environment (per cell)
# % required: no
# % guisection: Ricker
# %end
# %option
# % key: k_map
# % type: string
# % gisprompt: old,cell,raster
# % description: Map of carrying capacity of the environment (per cell)
# % required: no
# % guisection: Ricker
# %end
# %option
# % key: r_rick_value
# % type: double
# % description: Cell-specific fixed value of intrinsic rate of increase (Ricker)
# % required: no
# % multiple: no
# % guisection: Ricker
# %end
# %option
# % key: r_rick_map
# % gisprompt: old,cell,raster
# % description: Map of cell-specific intrinsic rate of increase (Ricker)
# % required: no
# % multiple: no
# % guisection: Ricker
# %end
# %option
# % key: population_patches
# % type: string
# % gisprompt: old,cell,raster
# % description: Optional raster map of patches of single populations. If provided, growth models are calculated based on these patches (patch-averaged r and cumulated k).
# % required: no
# % guisection: Optional
# %end
# %Option
# % key: seed
# % type: integer
# % required: no
# % multiple: no
# % description: fixed seed for random rounding
# % guisection: Optional
# %End
# %Flag
# % key: i
# % description: Calculate models with rounded integer values
# %end


# import required base modules
import sys
import os
import atexit
import math  # for function sqrt()

# import required grass modules
import grass.script as grass
import grass.script.array as garray


# import required numpy/scipy modules
import numpy


def cleanup():
    grass.debug(_("This is the cleanup part"))
    if tmp_map_rast or tmp_map_vect:
        grass.run_command(
            "g.remove",
            flags="fb",
            type="raster",
            name=[f + str(os.getpid()) for f in tmp_map_rast],
            quiet=True,
        )
        grass.run_command(
            "g.remove",
            flags="f",
            type="vector",
            name=[f + str(os.getpid()) for f in tmp_map_vect],
            quiet=True,
        )


def main():
    ############ DEFINITION CLEANUP TEMPORARY FILES ##############
    # global variables for cleanup
    global tmp_map_rast
    global tmp_map_vect

    tmp_map_rast = []
    tmp_map_vect = []

    ############ PARAMETER INPUT ##############
    # Check for correct input
    if str(options["exponential_output"]) == "" and str(options["ricker_output"]) == "":
        grass.fatal(_("Output name for a model is missing"))

    # Model parameters input
    t = int(options["timesteps"])

    # If populations patches are provided, otherwise single cell populations are used
    if options["population_patches"]:
        grass.run_command(
            "r.statistics2",
            base=options["population_patches"],
            cover=options["n_initial"],
            method="sum",
            output="n0_tmp_%d" % os.getpid(),
        )
    else:
        grass.run_command(
            "g.copy", raster=options["n_initial"] + "," + "n0_tmp_%d" % os.getpid()
        )

    tmp_map_rast.append("n0_tmp_")

    # Customized rounding function. Round based on a probability (p=digits after decimal point) to avoid "local stable states"
    # def prob_round(x, prec = 0):
    # 	fixup = numpy.sign(x) * 10**prec
    # 	x *= fixup
    # 	if options['seed']:
    # 		numpy.random.seed(seed=int(options['seed']))
    # 	round_func = int(x) + numpy.random.binomial(1,x-int(x))
    # 	return round_func/fixup
    # vprob_round = numpy.vectorize(prob_round)

    ################# Model Definiations #################
    # Model definitions modified from R scripts (http://www.mbr-pwrc.usgs.gov/workshops/unmarked/Rscripts/script-state-space.R)
    # Exponential Model

    def exponential_mod(n0, r, t):
        n = n0
        for t in range(t):
            n = 1.0 * n * numpy.exp(r)
            if flags["i"]:
                # n = vprob_round(n) #function not mature yet (takes partly long time, problems with NaNs)
                n = numpy.round(n)
        return n

    # Ricker Model
    def ricker_mod(n0, r, k, t):
        n = n0
        for t in range(t):
            numpy.seterr(invalid="ignore")
            n = 1.0 * n * numpy.exp(r * (1 - (n / k)))
            numpy.seterr(invalid="warn")
            if flags["i"]:
                # n = vprob_round(n) #function not mature yet (takes partly long time, problems with NaNs)
                n = numpy.round(n)
        return n

    ################# Exponential Model #################
    if options["exponential_output"]:
        # Check for correct input
        if options["r_exp_value"] and options["r_exp_map"]:
            grass.fatal(_("Provide either fixed value for r or raster map"))

        # Define r
        if options["r_exp_map"]:
            grass.debug(_("r_exp_map provided"))

            if options["population_patches"]:
                grass.run_command(
                    "r.statistics2",
                    base=options["population_patches"],
                    cover=options["r_exp_map"],
                    method="average",
                    output="r_exp_tmp_%d" % os.getpid(),
                )
            else:
                grass.run_command(
                    "g.copy",
                    raster=options["r_exp_map"] + "," + "r_exp_tmp_%d" % os.getpid(),
                )

            tmp_map_rast.append("r_exp_tmp_")

            r = garray.array("r_exp_tmp_%d" % os.getpid())

        elif options["r_exp_value"]:
            r = float(options["r_exp_value"])
        else:
            grass.fatal(_("No r value/map provided for exponential model"))

        # run model
        n0_map = garray.array("n0_tmp_%d" % os.getpid())
        exponential_map = garray.array()
        exponential_map[...] = exponential_mod(n0_map, r, t)
        ricker_map.write("exponential_output_tmp_%d" % os.getpid())
        tmp_map_rast.append("exponential_output_tmp_")

        # Retransform in case of patches
        if options["population_patches"]:
            grass.mapcalc(
                "$exponential_output = if($n0,(round(($n0*1.0/$n0_tmp)*$exponential_output_tmp)),null())",
                ricker_output=options["exponential_output"],
                n0=options["n_initial"],
                n0_tmp="n0_tmp_%d" % os.getpid(),
                ricker_output_tmp="exponential_output_tmp_%d" % os.getpid(),
            )

        else:
            grass.mapcalc(
                "$exponential_output = if($n0,$exponential_output_tmp,null())",
                exponential_output=options["exponential_output"],
                n0=options["n_initial"],
                exponential_output_tmp="exponential_output_tmp_%d" % os.getpid(),
            )

    ################# Ricker Model #################
    if options["ricker_output"]:
        # Check for correct input
        if options["r_rick_value"] and options["r_rick_map"]:
            grass.fatal(_("Provide either fixed value for r or raster map"))
        if options["k_value"] and options["k_map"]:
            grass.fatal(
                _("Provide either fixed value for carrying capacity (K) or raster map")
            )

        # Define r
        if options["r_rick_map"]:

            if options["population_patches"]:
                grass.run_command(
                    "r.statistics2",
                    base=options["population_patches"],
                    cover=options["r_rick_map"],
                    method="average",
                    output="r_rick_tmp_%d" % os.getpid(),
                )
            else:
                grass.run_command(
                    "g.copy",
                    raster=options["r_rick_map"] + "," + "r_rick_tmp_%d" % os.getpid(),
                )

            tmp_map_rast.append("r_rick_tmp_")

            r = garray.array("r_rick_tmp_%d" % os.getpid())

        elif options["r_rick_value"]:
            r = float(options["r_rick_value"])
        else:
            grass.fatal(_("No r value/map for Ricker model provided"))

        # Define k
        if options["k_map"]:
            if options["population_patches"]:
                grass.run_command(
                    "r.statistics2",
                    base=options["population_patches"],
                    cover=options["k_map"],
                    method="sum",
                    output="k_tmp_%d" % os.getpid(),
                )
            else:
                grass.run_command(
                    "g.copy", raster=options["k_map"] + "," + "k_tmp_%d" % os.getpid()
                )

            tmp_map_rast.append("k_tmp_")

            k = garray.array("k_tmp_%d" % os.getpid())

        elif options["k_value"]:
            k = float(options["k_value"])
        else:
            grass.fatal(_("No value/map for carrying capacity (k) provided"))

        # run model
        n0_map = garray.array("n0_tmp_%d" % os.getpid())
        ricker_map = garray.array()
        ricker_map[...] = ricker_mod(n0_map, r, k, t)
        ricker_map.write("ricker_output_tmp_%d" % os.getpid())
        tmp_map_rast.append("ricker_output_tmp_")

        # Retransform in case of patches
        if options["population_patches"]:
            grass.mapcalc(
                "$ricker_output = if($n0,(round(($n0*1.0/$n0_tmp)*$ricker_output_tmp)),null())",
                ricker_output=options["ricker_output"],
                n0=options["n_initial"],
                n0_tmp="n0_tmp_%d" % os.getpid(),
                ricker_output_tmp="ricker_output_tmp_%d" % os.getpid(),
            )

        else:
            grass.mapcalc(
                "$ricker_output = if($n0,$ricker_output_tmp,null())",
                ricker_output=options["ricker_output"],
                n0=options["n_initial"],
                ricker_output_tmp="ricker_output_tmp_%d" % os.getpid(),
            )

    return 0


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
