#!/usr/bin/env python3
############################################################################
#
# MODULE:       r.futures.simulation
# AUTHOR(S):    Anna Petrasova
# PURPOSE:      Wrapper for r.futures.pga for forward compatibility
# COPYRIGHT:    (C) 2022 by Anna Petrasova, and the GRASS Development Team
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
# % label: Wrapper for r.futures.pga to ensure forward compatibility.
# % description: Simulates landuse change using FUTure Urban-Regional Environment Simulation (FUTURES).
# % keyword: raster
# % keyword: patch growing
# % keyword: urban
# % keyword: landscape
# % keyword: modeling
# %end
# %flag
# % key: s
# % label: Generate random seed (result is non-deterministic)
# % description: Automatically generates random seed for random number generator (use when you don't want to provide the seed option)
# % guisection: Random numbers
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
# % key: devpot_params
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % label: CSV file with development potential parameters for each region
# % description: Each line should contain region ID followed by parameters (intercepts, development pressure, other predictors). First line is ignored, so it can be used for header
# % gisprompt: old,file,file
# % guisection: Potential
# %end
# %option
# % key: demand
# % type: string
# % required: yes
# % multiple: no
# % key_desc: name
# % description: CSV file with number of cells to convert for each step and subregion
# % gisprompt: old,file,file
# % guisection: Demand
# %end
# %option
# % key: separator
# % type: string
# % required: no
# % multiple: no
# % key_desc: character
# % label: Field separator
# % description: Separator used in input CSV files
# % answer: comma
# % gisprompt: old,separator,separator
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
# % key: discount_factor
# % type: double
# % required: yes
# % multiple: no
# % description: Discount factor of patch size
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
# % key: num_steps
# % type: integer
# % required: no
# % multiple: no
# % description: Number of steps to be simulated
# % guisection: Basic input
# %end
# %option
# % key: potential_weight
# % type: string
# % required: no
# % multiple: no
# % key_desc: name
# % label: Raster map of weights altering development potential
# % description: Values need to be between -1 and 1, where negative locally reducesprobability and positive increases probability.
# % gisprompt: old,cell,raster
# % guisection: Scenarios
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

import sys

import grass.script as gs


def main():
    options, flags = gs.parser()
    if flags["s"]:
        gs.run_command("r.futures.pga", flags="s", **options)
    else:
        gs.run_command("r.futures.pga", **options)
    return


if __name__ == "__main__":
    sys.exit(main())
