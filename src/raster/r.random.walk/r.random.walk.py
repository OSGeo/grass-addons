#!/usr/bin/env python3

############################################################################
#
# MODULE:       r.random.walk
# AUTHOR:       Corey T. White, Center for Geospatial Analytics, North Carolina State University
# PURPOSE:      Performs a random walk on a raster surface.
# COPYRIGHT:    (C) 2022 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

#%module
#% description: Performs a 2D random walk inside the computational region and returns the resulting walk.
#% keyword: raster
#% keyword: random
#% keyword: walk
#% keyword: surface
#% keyword: parallel
#%end

#%flag
#% key: revisit
#% description: Allow walker to revisit a cell.
#% guisection: Parameters
#%end

#%flag
#% key: seed
#% description: Generate random seed (result is non-deterministic).
#%end

#%flag
#% key: tpath
#% description: Each walker starts from the same point.
#%end

#%option G_OPT_R_OUTPUT
#%end

#%option
#% key: steps
#% type: integer
#% required: no
#% multiple: no
#% description: How many steps to take during walk.
#% answer: 100000
#% guisection: Parameters
#%end

#%option
#% key: directions
#% type: string
#% required: no
#% multiple: no
#% options: 4, 8
#% description: How many directions should be used during walk.
#% answer: 4
#% guisection: Parameters
#%end

#%option G_OPT_MEMORYMB
#%end

#%option
#% key: seed
#% type: integer
#% required: no
#% multiple: no
#% description: Seed for random number generator
#%end

#%option G_OPT_M_NPROCS
#%end

#%option
#% key: nwalkers
#% type: integer
#% required: no
#% multiple: no
#% answer: 10
#% description: Number of walkers, only used when parallel is enabled
#%end

import atexit
import concurrent.futures
import math
import os
import random
import sys
import time

import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.pygrass import raster
from grass.pygrass.gis.region import Region
from grass.script.core import gisenv

# import numpy as np
TMP_SMOOTH_RASTERS = []
TMP_RASTERS = []
PREFIX = "r_random_walk_temp_walk_"


def cleanup():
    if TMP_RASTERS:
        gs.run_command(
            "g.remove",
            type="raster",
            pattern="r_random_walk_temp_walk_*",
            flags="f",
            quiet=True,
        )


class GetOutOfLoop(Exception):
    """
    Throw to break out of nested loop.
    """

    pass


## TODO: Rewrite this section to use differnt random distributions using values [0,1]
def take_step(current_position, num_dir, black_list=None):
    """
    Calculates the next position of walker using either 4 or 8 possible directions.
    :param list[row, column] current_position: A list with current row and column as integers.
    :param int num_dir: The number of directions used in walk. Value must be either 4 or 8.
    :param list[int] black_list: List of directions that the walker cannot take ranging from 0 - 7.
    :return list[row, column] new_position
    """
    if black_list is None:
        black_list = []

    if num_dir not in [4, 8]:
        raise ValueError(f"Unsupported num_dir Recieved: {num_dir}")

    direction = random.choice(
        [ele for ele in range(num_dir + 1) if ele not in black_list]
    )

    current_row = current_position[0]
    current_column = current_position[1]
    new_position = []
    # # 4 - directions
    # direction = random.randint(0, num_dir)
    if direction == 0:
        # Stay in place
        new_position = current_position
    elif direction == 1:
        # Move up (N)
        new_position = [current_row + 1, current_column]
    elif direction == 2:
        # Move right (E)
        new_position = [current_row, current_column + 1]
    elif direction == 3:
        # Move Down (S)
        new_position = [current_row - 1, current_column]
    elif direction == 4:
        # Move Left(W)
        new_position = [current_row, current_column - 1]
    elif direction == 5:
        # Move Top Right (NE)
        new_position = [current_row + 1, current_column + 1]
    elif direction == 6:
        # Move Bottom Right (SE)
        new_position = [current_row - 1, current_column + 1]
    elif direction == 7:
        # Move Bottom Left (SW)
        new_position = [current_row - 1, current_column - 1]
    elif direction == 8:
        # Move Top Left (NW)
        new_position = [current_row + 1, current_column - 1]
    else:
        raise ValueError(f"Unsupported Direction Recieved: {direction}")

    # stepx = random.randint(0, 2) -1
    # stepy = random.randint(0, 2) -1
    # current_row += stepy
    # current_column += stepx
    # new_position = [current_row, current_column]

    return {"position": new_position, "direction": direction}


def cell_visited(rast, position):
    """
    Checks if a cell was previously visited during walk.
    :param RasterSegment rast: The new raster that walk results are written.
    :param list[row, column]: The position to check.
    :return bool
    """
    cell_value = rast.get(position[0], position[1])
    # Positions with a value greater than zero are visited.
    return cell_value > 0


def walker_is_stuck(tested_directions, num_directions):
    """
    Test if walker has no more move to consider and is stuck.
    :param list tested_directions: List of directions previously tested
    :param int num_directions: The total number of possible directions (4 or 8)
    :return bool
    """
    return len(tested_directions) == num_directions


def find_new_path(walk_output, current_pos, new_position, num_directions, step):
    """
    Finds a cell that walker has not touched yet.
    :param RasterSegment walk_output: The raster being written
    :param list[row, column] current_position: The current position of the walker.
    :param Dict{position: list[row, column], direction: int} new_position: Previously test position
    :param int num_directions: The total number of directions walker can travel 4 or 8.
    :param int step: The current step the walker is on.
    """
    tested_directions = []
    visited = cell_visited(walk_output, new_position["position"])
    tested_directions.append(new_position["direction"])

    while visited:
        if walker_is_stuck(tested_directions, num_directions):
            gs.message(_("Walker stuck on step {0}".format(step)))
            raise GetOutOfLoop
        else:
            # continue to check cells for an unvisited cell until one is found or walker is stuck
            new_position = take_step(current_pos, num_directions, tested_directions)
            tested_directions.append(new_position["direction"])
            visited = cell_visited(walk_output, new_position["position"])

    return new_position


def avoid_boundary(position, boundary):
    """
    Generates a list of directions to avoid, so that the walk can continue in bounds.
    :param Dict{position: list[row, column], direction: int} position: The last tried position and directions.
    :param list[row, column] boundary: The maximum row and column values for the region.
    :return list[int]: A list of directions to avoid, so the bioundary is not crossed.
    """

    brows, bcols = boundary
    prow, pcol = position["position"]

    avoid_directions = []
    if prow >= brows:
        # No North Moves
        avoid_directions.extend([1, 5, 8])
    if prow < 0:
        # No South Moves
        avoid_directions.extend([3, 6, 7])
    if pcol >= bcols:
        # No East Moves
        avoid_directions.extend([2, 5, 6])
    if pcol < 0:
        # No West Moves
        avoid_directions.extend([4, 7, 8])

    return avoid_directions


def random_walk(
    num_directions, boundary, steps, revisit, start_position, memory, walk_output_name
):
    """
    Calulates a random walk on a raster surface.
    :param int num_directions: The number of directions to consider on walk.
        Values represtent either 4 or 8 direction walks and must be set as
        either 4 or 8.
    :param list[row, column] boundary:
    :param RasterSegment walk_output:
    :param int steps:
    :param bool revisit: Determines if the walker can revisit a cell it has
        already visited.
    :param bool:list[row, column] start_position: A start position for the
        walk to be used for all concurrent walks or False to generate a new start posisition for each walker.
    :param int memory: The total memory assigned to the RasterSegment.
    :param string walk_output_name: The name of raster file getting created.
    :return RasterSegment
    """

    walk_output = raster.RasterSegment(walk_output_name, maxmem=memory)
    walk_output.open("w", mtype="FCELL", overwrite=True)

    def _create_walker(start_pos):
        try:
            walk_output.put(start_pos[0], start_pos[1], 1)
        except (AttributeError, ValueError) as err:
            gs.message(_(err))

        current_pos = start_pos
        try:
            for step in range(steps + 1):
                # Take a randomly selected step in a direction
                out_of_bounds_directions = []
                new_position = take_step(current_pos, num_directions)
                while out_of_bounds(new_position["position"], boundary):
                    avoid_directions = avoid_boundary(new_position, boundary)
                    # Add to list of direction to avoid during the next step.
                    out_of_bounds_directions.extend(avoid_directions)
                    new_position = take_step(
                        current_pos, num_directions, black_list=out_of_bounds_directions
                    )

                if not revisit:
                    # Don't allow walker to revisit same cell.
                    new_position = find_new_path(
                        walk_output, current_pos, new_position, num_directions, step
                    )

                value = walk_output.get(
                    new_position["position"][0], new_position["position"][1]
                )
                # Add up times visited
                walk_output.put(
                    new_position["position"][0], new_position["position"][1], value + 1
                )

                # Update Position
                current_pos = new_position["position"]

        except GetOutOfLoop:
            # Mark the last step if walker gets stuck
            walk_output[current_pos[0], current_pos[1]] = 3
            pass

    # Select Random Starting Cell in Matrix
    if start_position:
        # Sample the same path with each walker
        _create_walker(start_position)
    else:
        # Select a new starting point with each walker
        start_pos = starting_position(boundary[0], boundary[1])
        _create_walker(start_pos)

    walk_output.close()

    return walk_output_name


def starting_position(surface_rows, surface_columns):
    """
    Calculates a random starting position for walk.
    :param int surface_rows: The total number of rows to consider.
    :param int surface_columns: The total number of columns to consider.
    :return list[row, column]
    """
    start_row = random.randint(0, surface_rows)
    start_column = random.randint(0, surface_columns)
    return [start_row, start_column]


def out_of_bounds(position, region):
    brows, bcols = region
    prow, pcol = position

    if prow >= brows or prow < 0 or pcol >= bcols or pcol < 0:
        return True
    else:
        return False


def run_paralle(
    tmp_rasters,
    processes,
    directions,
    boundary,
    steps,
    revisit,
    path_sampling,
    memory,
    chunks,
):
    gs.message(_("Smoothed Walk"))
    max_cpus = os.cpu_count() - 1
    gs.message(_("Max CPUs: {0}, Used CPUs: {1}".format(max_cpus, processes)))
    start_pos = False
    if path_sampling:
        start_pos = starting_position(boundary[0], boundary[1])

    with concurrent.futures.ProcessPoolExecutor(max_workers=processes) as executor:
        future_to_raster = {
            executor.submit(
                random_walk,
                directions,
                boundary,
                steps,
                revisit,
                start_pos,
                memory,
                tmpfile,
            ): tmpfile
            for tmpfile in tmp_rasters
        }

        return future_to_raster


def get_chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i : i + n]


def is_parallel(processes):
    """
    Checks if the module should be ran in parallel based on users nproc setting.
    param: int processes: The number of processes defined by the nproc option
    return: bool
    """
    return True if processes > 1 else False


def main():
    start = time.time()
    output_raster = options["output"]

    steps = int(options["steps"])

    directions_option = options["directions"]

    # Set numerical values for directions
    directions = int(directions_option)

    memory = options["memory"]

    # Only set the random seed if s flag is set to false
    if flags["s"] != True:
        seed = options["seed"]
        random.seed(seed)

    # check for revisit flag
    revisit = flags["r"]

    ## Same as the comment above, I'm not sure if using an existing raster or computational region is prefered yet.
    # surface = raster.RasterRow(input_raster)
    # surface.open()
    # surface_rows = surface._rows
    # surface_columns = surface._cols

    reg = Region()
    cols = reg.cols
    rows = reg.rows
    gs.message(_("Region with {0} rows and {1} columns".format(rows, cols)))
    boundary = [rows, cols]
    path_sampling = flags["t"]
    processes = int(options["nprocs"])
    # Run as parallel if user choses to use multiple processes
    parallel = is_parallel(processes)
    if parallel:
        smooth = int(options["nwalkers"])
        _tmp_rasters = [f"{PREFIX}{i}" for i in range(0, smooth)]
        TMP_RASTERS.append(_tmp_rasters)
        chunks_n = math.ceil(smooth / processes)
        # Divide memory into equal chunks for each of the processes
        mem_for_process = math.floor(int(memory) / processes)
        gs.message(_("Memory Per Process: {0}".format(mem_for_process)))
        chunks_lst = list(get_chunks(_tmp_rasters, math.ceil(smooth / chunks_n)))
        chunks = len(chunks_lst)
        futures = run_paralle(
            _tmp_rasters,
            processes,
            directions,
            boundary,
            steps,
            revisit,
            path_sampling,
            mem_for_process,
            chunks,
        )

        for future in concurrent.futures.as_completed(futures):
            try:
                data = future.result()
                TMP_SMOOTH_RASTERS.append(data)
            except Exception as exc:
                gs.message(_("generated an exception: {0}".format(exc)))
            else:
                continue

        gs.message(_("Averaging: {0} Rasters".format(len(TMP_SMOOTH_RASTERS))))
        if len(TMP_SMOOTH_RASTERS) > 0:
            # 1024 is the soft limit for most computures for number of allowed open files
            if len(TMP_SMOOTH_RASTERS) >= 1024:
                gs.run_command(
                    "r.series",
                    input=TMP_SMOOTH_RASTERS,
                    output=output_raster,
                    method="average",
                    flags="z",
                )
            else:
                gs.run_command(
                    "r.series",
                    input=TMP_SMOOTH_RASTERS,
                    output=output_raster,
                    method="average",
                )

    else:
        gs.message(_("Single Walk"))
        random_walk(directions, boundary, steps, revisit, False, memory, output_raster)

    # cleanup()
    end = time.time()
    gs.message(_("Runtime of the program is {0}".format(end - start)))


if __name__ == "__main__":
    options, flags = gs.parser()

    atexit.register(cleanup)  # Doesn't seem to play well with multiprocessing...
    sys.exit(main())
