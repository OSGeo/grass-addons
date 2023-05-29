#!/usr/bin/env python
#
#########################################################################
#
# MODULE:     r.hydro.flatten
#
# AUTHOR(S):  Anna Petrasova <kratochanna gmail com>
#
# PURPOSE:    Derive elevation of water bodies for hydro-flattening
#
# COPYRIGHT:  (C) 2023 by Anna Petrasova, and the GRASS Development Team
#
#             This program is free software under the GNU General Public
#             License (>=v2). Read the COPYING file that comes with GRASS
#             for details.
#
#########################################################################

# %module
# % description: Derive elevation of water bodies for hydro-flattening
# % keyword: raster
# % keyword: elevation
# % keyword: hydrology
# % keyword: lidar
# % keyword: LIDAR
# %end
# %option G_OPT_R_INPUT
# % key: input
# % description: Raster map of binned lidar point elevation
# %end
# %option G_OPT_R_OUTPUT
# % key: water_elevation
# % description: Represents single elevation value for each water body
# % label: Raster map of derived water elevation
# %end
# %option G_OPT_R_OUTPUT
# % key: water_elevation_stddev
# % description: Raster map of derived water elevation standard deviation
# %end
# %option
# % key: percentile
# % type: double
# % required: yes
# % description: Percentile of elevation to determine water level
# % answer: 5
# %end
# %option
# % key: min_size
# % type: integer
# % required: no
# % description: Minimum size of areas in map units
# %end
# %flag
# % key: k
# % description: Keep intermediate results
# %end

import os
import sys
import atexit
from math import sqrt

import grass.script as gs

RAST_REMOVE = []


def cleanup():
    if RAST_REMOVE:
        gs.run_command("g.remove", flags="fb", type="raster", name=RAST_REMOVE)


def get_tmp_name(basename):
    name = gs.append_node_pid(basename)
    RAST_REMOVE.append(name)
    return name


def main():
    options, flags = gs.parser()
    keep = flags["k"]
    if keep:

        def get_name(basename):
            return f"intermediate_{basename}"

    else:

        def get_name(basename):
            name = gs.append_node_pid(basename)
            RAST_REMOVE.append(name)
            return name

    ground = options["input"]
    size_threshold = options["min_size"]
    if size_threshold:
        size_threshold = int(size_threshold)
    else:
        size_threshold = None
    # r.fill.stats settings
    filling_distance = 3
    filling_cells = 6
    # we set r.buffer to have 1 more 1-cell band than grown by r.fill.stats
    # and the category of that strip is number of distance bands + 1
    buffer_last_strip = filling_distance + 2
    region = gs.region()
    region_m = gs.parse_command("g.region", flags="gm")
    resolution_m = (float(region_m["nsres"]) + float(region_m["ewres"])) / 2
    tmp_rfillstats = get_name("rfillstats")
    gs.run_command(
        "r.fill.stats",
        flags="k",
        input=ground,
        output=tmp_rfillstats,
        distance=filling_distance,
        cells=filling_cells,
    )
    tmp_holes = get_name("holes")
    gs.mapcalc(f"{tmp_holes} = if(isnull({tmp_rfillstats}), 1, null())")
    tmp_buffer = get_name("buffer")
    gs.run_command(
        "r.buffer",
        input=tmp_holes,
        output=tmp_buffer,
        distances=[x * resolution_m for x in range(1, buffer_last_strip)],
        units="meters",
    )
    tmp_reclass_for_clump = get_name("reclass_for_clump")
    gs.write_command(
        "r.reclass",
        input=tmp_buffer,
        output=tmp_reclass_for_clump,
        rules="-",
        stdin=f"1 thru {buffer_last_strip} = 1",
    )
    tmp_clump = get_name("clump")
    gs.run_command("r.clump", flags="d", input=tmp_reclass_for_clump, output=tmp_clump)
    tmp_strip = get_name("strip")
    gs.mapcalc(
        f"{tmp_strip} = if ({tmp_buffer} == {buffer_last_strip}, {tmp_clump}, null())"
    )
    tmp_water_elevation = get_name("water_elevation")
    gs.run_command(
        "r.stats.quantile",
        base=tmp_strip,
        cover=tmp_rfillstats,
        percentiles=options["percentile"],
        output=tmp_water_elevation,
    )
    tmp_water_stddev = get_name("water_stddev")
    gs.run_command(
        "r.stats.zonal",
        base=tmp_strip,
        cover=tmp_rfillstats,
        method="stddev",
        output=tmp_water_stddev,
    )
    tmp_water_elevation_dist = get_name("water_elevation_dist")
    gs.run_command(
        "r.grow.distance", input=tmp_water_elevation, value=tmp_water_elevation_dist
    )
    tmp_water_stddev_dist = get_name("water_stddev_dist")
    gs.run_command(
        "r.grow.distance", input=tmp_water_stddev, value=tmp_water_stddev_dist
    )
    tmp_water_elevation_dist_res = get_name("water_elevation_dist_res")
    gs.mapcalc(
        f"{tmp_water_elevation_dist_res} = if ({tmp_buffer} < {buffer_last_strip}, "
        f"{tmp_water_elevation_dist}, null())"
    )
    tmp_water_stddev_dist_res = get_name("water_stddev_dist_res")
    gs.mapcalc(
        f"{tmp_water_stddev_dist_res} = if ({tmp_buffer} < {buffer_last_strip}, "
        f"{tmp_water_stddev_dist}, null())"
    )
    if size_threshold:
        size_threshold /= region["nsres"] * region["ewres"]
        tmp_reclass = get_name("reclass")
        gs.write_command(
            "r.reclass",
            input=tmp_water_elevation_dist_res,
            output=tmp_reclass,
            rules="-",
            stdin="* = 1",
        )
        tmp_clump_reclass = get_name("clump_reclass")
        gs.run_command("r.clump", input=tmp_reclass, output=tmp_clump_reclass)
        tmp_size = get_name("size")
        gs.run_command(
            "r.stats.zonal",
            base=tmp_clump_reclass,
            cover=tmp_reclass,
            method="sum",
            output=tmp_size,
        )
        gs.mapcalc(
            f"{options['water_elevation']} = if ({tmp_size} > {size_threshold}, {tmp_water_elevation_dist_res}, null())"
        )
        gs.mapcalc(
            f"{options['water_elevation_stddev']} = if ({tmp_size} > {size_threshold}, {tmp_water_stddev_dist_res}, null())"
        )
    else:
        gs.mapcalc(f"{options['water_elevation']} = {tmp_water_elevation_dist_res}")
        gs.mapcalc(f"{options['water_elevation_stddev']} = {tmp_water_stddev_dist_res}")
    gs.run_command("r.colors", map=options["water_elevation"], raster=ground)
    gs.run_command("r.colors", map=options["water_elevation_stddev"], color="reds")
    gs.raster_history(options["water_elevation"])
    gs.raster_history(options["water_elevation_stddev"])


if __name__ == "__main__":
    atexit.register(cleanup)
    sys.exit(main())
