#!/usr/bin/env python3
############################################################################
#
# MODULE:       r.futures.parallelpga
# AUTHOR(S):    Anna Petrasova
# PURPOSE:      Run r.futures.simulation in parallel
# COPYRIGHT:    (C) 2016 by Anna Petrasova, and the GRASS Development Team
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
############################################################################

# %module
# % label: Simulates landuse change using FUTURES (r.futures.simulation) on multiple CPUs in parallel.
# % description: Module uses Patch-Growing Algorithm (PGA) to simulate urban-rural landscape structure development.
# % keyword: raster
# % keyword: patch growing
# % keyword: urban
# % keyword: landscape
# % keyword: modeling
# %end
# %flag
# % key: d
# % label: Runs each subregion separately
# % description: r.futures.simulation runs for each subregion and after all subregions are completed, the results are patched together
# % guisection: Parallel
# %end
# %option
# % key: nprocs
# % type: integer
# % required: yes
# % multiple: no
# % answer: 1
# % description: Number of processes to run in parallel
# % guisection: Parallel
# %end
# %option
# % key: repeat
# % type: integer
# % required: yes
# % multiple: no
# % answer: 10
# % description: Number of times stochastic simulation is repeated
# % guisection: Parallel
# %end
# %option
# % key: developed
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: Raster map of developed areas (=1), undeveloped (=0) and excluded (no data)
# % gisprompt: old,cell,raster
# % guisection: Basic input
# %end
# %option
# % key: subregions
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: Raster map of subregions
# % gisprompt: old,cell,raster
# % guisection: Basic input
# %end
# %option
# % key: subregions_potential
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: Raster map of subregions used with potential file
# % description: If not specified, the raster specified in subregions parameter is used
# % gisprompt: old,cell,raster
# % guisection: Potential
# %end
# %option
# % key: output
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: State of the development at the end of simulation
# % gisprompt: new,cell,raster
# % guisection: Output
# %end
# %option
# % key: output_series
# % type: string
# % required: no
# % multiple: no
# % key_desc: basename
# % label: Basename for raster maps of development generated after each step
# % description: Name for output basename raster map(s)
# % gisprompt: new,cell,raster
# % guisection: Output
# %end
# %option
# % key: output_density
# % type: string
# % required: no
# % multiple: no
# % key_desc: basename
# % label: Basename for raster maps of density generated after each step
# % description: Name for output basename raster map(s)
# % gisprompt: new,cell,raster
# % guisection: Output
# %end
# %option
# % key: num_steps
# % type: integer
# % required: no
# % multiple: no
# % description: Number of steps to be simulated
# % guisection: Basic input
# %end
# %option
# % key: predictors
# % type: string
# % required: yes
# % multiple: yes
# % key_desc: name
# % label: Names of predictor variable raster maps
# % description: Listed in the same order as in the development potential table
# % gisprompt: old,cell,raster
# % guisection: Potential
# %end
# %option
# % key: devpot_params
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % label: Development potential parameters for each region
# % description: Each line should contain region ID followed by parameters (intercepts, development pressure, other predictors). Values are separated by tabs. First line is ignored, so it can be used for header
# % gisprompt: old,file,file
# % guisection: Potential
# %end
# %option
# % key: development_pressure
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: Raster map of development pressure
# % gisprompt: old,cell,raster
# % guisection: Development pressure
# %end
# %option
# % key: n_dev_neighbourhood
# % type: integer
# % required: yes
# % multiple: no
# % description: Size of square used to recalculate development pressure
# % guisection: Development pressure
# %end
# %option
# % key: development_pressure_approach
# % type: string
# % required: yes
# % multiple: no
# % options: occurrence,gravity,kernel
# % description: Approaches to derive development pressure
# % answer: gravity
# % guisection: Development pressure
# %end
# %option
# % key: gamma
# % type: double
# % required: yes
# % multiple: no
# % description: Influence of distance between neighboring cells
# % guisection: Development pressure
# %end
# %option
# % key: scaling_factor
# % type: double
# % required: yes
# % multiple: no
# % description: Scaling factor of development pressure
# % guisection: Development pressure
# %end
# %option
# % key: demand
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: Control file with number of cells to convert
# % gisprompt: old,file,file
# % guisection: Demand
# %end
# %option
# % key: population_demand
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: CSV file with population size to accommodate
# % gisprompt: old,file,file
# % guisection: Demand
# %end
# %option
# % key: discount_factor
# % type: double
# % required: yes
# % multiple: no
# % description: Discount factor of patch size
# % guisection: PGA
# %end
# %option
# % key: compactness_mean
# % type: double
# % required: yes
# % multiple: no
# % description: Mean value of patch compactness to control patch shapes
# % guisection: PGA
# %end
# %option
# % key: compactness_range
# % type: double
# % required: yes
# % multiple: no
# % description: Range of patch compactness to control patch shapes
# % guisection: PGA
# %end
# %option
# % key: num_neighbors
# % type: integer
# % required: yes
# % multiple: no
# % options: 4,8
# % description: The number of neighbors to be used for patch generation (4 or 8)
# % answer: 4
# % guisection: PGA
# %end
# %option
# % key: seed_search
# % type: string
# % required: yes
# % multiple: no
# % options: random,probability
# % description: The way location of a seed is determined (1: uniform distribution 2: development probability)
# % answer: probability
# % guisection: PGA
# %end
# %option
# % key: patch_sizes
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: File containing list of patch sizes to use
# % gisprompt: old,file,file
# % guisection: PGA
# %end
# %option
# % key: density
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Raster map of population density
# % gisprompt: old,cell,raster
# % guisection: Density
# %end
# %option
# % key: density_capacity
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Raster map of maximum capacity
# % gisprompt: old,cell,raster
# % guisection: Density
# %end
# %option
# % key: redevpot_params
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: CSV file with redevelopment potential parameters for each region
# % description: Each line should contain region ID followed by parameters (intercepts, development pressure, other predictors).
# % gisprompt: old,file,file
# % guisection: Density
# %end
# %option
# % key: redevelopment_lag
# % type: integer
# % required: no
# % multiple: no
# % options: 1-
# % description: Number of steps before redevelopment can happen again in a cell developed during simulation
# % guisection: Density
# %end
# %option
# % key: incentive_power
# % type: double
# % required: no
# % multiple: no
# % options: 0-10
# % label: Exponent to transform probability values p to p^x to simulate infill vs. sprawl
# % description: Values > 1 encourage infill, < 1 urban sprawl
# % answer: 1
# % guisection: Scenarios
# %end
# %option G_OPT_R_INPUT
# % key: potential_weight
# % required: no
# % label: Raster map of weights altering development potential
# % description: Values need to be between -1 and 1, where negative locally reduces probability and positive increases probability.
# % guisection: Scenarios
# %end
# %option
# % key: redistribution_matrix
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Matrix containing probabilities of moving from one subregion to another
# % gisprompt: old,file,file
# % guisection: Climate scenarios
# %end
# %option
# % key: redistribution_output
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Base name for output file containing matrix of pixels moved from one subregion to another
# % gisprompt: new,file,file
# % guisection: Climate scenarios
# %end
# %option
# % key: hand
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Height Above Nearest Drainage raster
# % gisprompt: old,cell,raster
# % guisection: Climate scenarios
# %end
# %option
# % key: hand_percentile
# % type: integer
# % required: no
# % multiple: no
# % options: 0-100
# % description: Percentile of HAND values within inundated area for depth estimation
# % answer: 90
# % guisection: Climate scenarios
# %end
# %option
# % key: flood_maps_file
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: CSV file with (step, return period, map of depth) or (step, map of return period)
# % gisprompt: old,file,file
# % guisection: Climate scenarios
# %end
# %option
# % key: flood_logfile
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: CSV file with (step, HUC ID, flood probability)
# % gisprompt: new,file,file
# % guisection: Climate scenarios
# %end
# %option
# % key: huc
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Raster of HUCs
# % gisprompt: old,cell,raster
# % guisection: Climate scenarios
# %end
# %option
# % key: adaptive_capacity
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Adaptive capacity raster
# % gisprompt: old,cell,raster
# % guisection: Climate scenarios
# %end
# %option
# % key: adaptation
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: Raster map of current adaptations for specific flood return periods (e.g. 5, 20)
# % description: Name of input raster map
# % gisprompt: old,cell,raster
# % guisection: Climate scenarios
# %end
# %option
# % key: output_adaptation
# % type: string
# % required: no
# % multiple: no
# % key_desc: basename
# % label: Basename for raster maps of adaptation generated after each step
# % description: Name for output basename raster map(s)
# % gisprompt: new,cell,raster
# % guisection: Output
# %end
# %option
# % key: depth_damage_functions
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: CSV file with depth-damage function
# % gisprompt: old,file,file
# % guisection: Climate scenarios
# %end
# %option
# % key: ddf_subregions
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % description: Subregions raster for depth-damage functions
# % gisprompt: old,cell,raster
# % guisection: Climate scenarios
# %end
# %option
# % key: random_seed
# % type: integer
# % required: no
# % multiple: no
# % label: Seed for random number generator
# % description: The same seed can be used to obtain same results or random seed can be generated by other means.
# % guisection: Random numbers
# %end
# %option
# % key: memory
# % type: double
# % required: no
# % multiple: no
# % description: Memory in GB
# %end


import os
import sys
import atexit
from multiprocessing import Pool

import grass.script as gs
from grass.exceptions import CalledModuleError

TMP_RASTERS = []
PREFIX = "tmprfuturesparallelpga"


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove", type="raster", name=TMP_RASTERS, flags="f", quiet=True
        )


def futures_process(params):
    repeat, seed, cat, options = params
    try:
        if cat:
            gs.message(
                _("Running simulation {s}/{r} for subregion {sub}").format(
                    s=seed, r=repeat, sub=cat
                )
            )
            env = os.environ.copy()
            env["GRASS_REGION"] = gs.region_env(raster=PREFIX + cat, zoom=PREFIX + cat)
            gs.run_command("r.futures.simulation", env=env, **options)
        else:
            gs.message(_("Running simulation {s}/{r}").format(s=seed, r=repeat))
            gs.run_command("r.futures.simulation", **options)
    except (KeyboardInterrupt, CalledModuleError):
        return


def split_subregions(expr):
    try:
        gs.mapcalc(expr)
    except (KeyboardInterrupt, CalledModuleError):
        return


def main():
    repeat = int(options.pop("repeat"))
    nprocs = int(options.pop("nprocs"))
    subregions = options["subregions"]
    tosplit = flags["d"]
    # filter unused optional params
    for key in list(options.keys()):
        if options[key] == "":
            options.pop(key)
    if tosplit and "output_series" in options:
        gs.fatal(
            _(
                "Parallelization on subregion level is not supported together with <output_series> option"
            )
        )

    if (
        not gs.overwrite()
        and gs.list_grouped("raster", pattern=options["output"] + "_run1")[
            gs.gisenv()["MAPSET"]
        ]
    ):
        gs.fatal(
            _(
                "Raster map <{r}> already exists."
                " To overwrite, use the --overwrite flag"
            ).format(r=options["output"] + "_run1")
        )
    global TMP_RASTERS
    cats = []
    if tosplit:
        gs.message(_("Splitting subregions"))
        cats = (
            gs.read_command("r.stats", flags="n", input=subregions).strip().splitlines()
        )
        if len(cats) < 2:
            gs.fatal(
                _("Not enough subregions to split computation. Do not use -d flag.")
            )
        mapcalcs = []
        for cat in cats:
            new = PREFIX + cat
            TMP_RASTERS.append(new)
            mapcalcs.append(
                "{new} = if({sub} == {cat}, {sub}, null())".format(
                    sub=subregions, cat=cat, new=new
                )
            )
        pool = Pool(nprocs)
        p = pool.map_async(split_subregions, mapcalcs)
        try:
            p.wait()
        except (KeyboardInterrupt, CalledModuleError):
            return

    options_list = []
    for i in range(repeat):
        if cats:
            for cat in cats:
                op = options.copy()
                op["random_seed"] = i + 1
                if "output_series" in op:
                    op["output_series"] += "_run" + str(i + 1) + "_" + cat
                    TMP_RASTERS.append(op["output_series"])
                op["output"] += "_run" + str(i + 1) + "_" + cat
                op["subregions"] = PREFIX + cat
                options_list.append((repeat, i + 1, cat, op))
                TMP_RASTERS.append(op["output"])
        else:
            op = options.copy()
            op["random_seed"] = i + 1
            if "output_series" in op:
                op["output_series"] += "_run" + str(i + 1)
            if "redistribution_output" in op:
                op["redistribution_output"] += "_run" + str(i + 1)
            if "output_adaptation" in op:
                op["output_adaptation"] += "_run" + str(i + 1)
            if "flood_logfile" in op:
                path, ext = os.path.splitext(op["flood_logfile"])
                op["flood_logfile"] = path + "_run" + str(i + 1) + ext
            op["output"] += "_run" + str(i + 1)
            options_list.append((repeat, i + 1, None, op))

    pool = Pool(nprocs)
    p = pool.map_async(futures_process, options_list)
    try:
        p.wait()
    except (KeyboardInterrupt, CalledModuleError):
        return

    if cats:
        gs.message(_("Patching subregions"))
        for i in range(repeat):
            patch_input = [
                options["output"] + "_run" + str(i + 1) + "_" + cat for cat in cats
            ]
            gs.run_command(
                "r.patch",
                input=patch_input,
                output=options["output"] + "_run" + str(i + 1),
            )

    return 0


if __name__ == "__main__":
    options, flags = gs.parser()
    atexit.register(cleanup)
    sys.exit(main())
