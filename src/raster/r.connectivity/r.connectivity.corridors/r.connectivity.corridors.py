#!/usr/bin/env python
# -*- coding: UTF-8 -*-

"""
MODULE:       r.connectivity.corridors
AUTHOR(S):    Stefan Blumentrath <stefan dot blumentrath at nina dot no >
PURPOSE:      Compute corridors between habitat patches of an input-
              layer based on distance raster maps produced by
              r.connecivity.distance.
              Corridor-importance can be evaluated based on results from
              r.connectivity.network.

              Recently, graph-theory has been characterised as an
              efficient and useful tool for conservation planning
              (e.g. Bunn et al. 2000, Calabrese & Fagan 2004,
              Minor & Urban 2008, Zetterberg et. al. 2010).
              As a part of the r.connectivity.* toolset,
              r.connectivity.distance is intended to make graph-theory
              more easily available to conservation planning.

              r.connectivity.corridors is the 3rd tool of the
              r.connectivity.* toolchain.

              r.connectivity.corridors loops through the attribute-table
              of the edge-output vector map from r.connectivity.network
              and computes the corridor for each edge of a user-defined
              set of edges. r.connectivity.corridors can account for the
              importance of the corridors for the entire network by
              reclassifying them with regards to network measures from
              r.connectivity.network.

              Finally, all individual corridors are being put together
              using r.series. In this step the values of the cells in
              all corridor maps are summed up, which indicates the
              importance of an area (raster cell) for the network of the
              given patches (either the number of corridors a cell is
              part of, or other graph-theoretical measures for corridor
              importance).

              !!!Corridors are only computed for an undirected graph.!!!

              Output raster maps are named according to a user defined
              prefix and suffix.

COPYRIGHT:    (C) 2011 by the Norwegian Institute for Nature Research
                  (NINA)

              This program is free software under the GNU General Public
              License (>=v2). Read the file COPYING that comes with
              GRASS for details.

########################################################################

REQUIREMENTS:

"""

#%Module
#% description: Compute corridors between habitat patches of an input-layer based on (cost) distance raster maps
#% keyword: raster
#% keyword: vector
#% keyword: corridor
#% keyword: cost distance
#% keyword: least cost paths
#%End

#%option G_OPT_V_INPUT
#% required: yes
#% key_desc: Result from r.connectivity.network containing edge measures
#% description: Name of the table containing edge measures from r.connectivity.network
#%end

#%option G_OPT_V_FIELD
#% required: yes
#% answer: 1
#% description: layer containing patch geometries
#%end

#%Option G_OPT_DB_COLUMNS
#% key: weights
#% type: string
#% required: no
#% multiple: yes
#% key_desc: Column names
#% description: Column names separated by commas
#%End

#%Option G_OPT_DB_where
#% key: where
#% required: no
#% key_desc: where (SQL statement)
#% description: where conditions of an SQL statement without 'where' keyword. (example: cf_mst_ud = 1 or cf_eb_ud > 100)
#%End

#%option
#% key: suffix
#% type: string
#% description: Output suffix for corridor summary result
#% required : yes
#%end

#%option
#% key: corridor_tolerance
#% type: double
#% description: Tolerance for deviation from (cost) distance within corridors (in %)
#% required : no
#% answer : 0.0
#%end

#%flag
#% key: s
#% description: Show edges selected by where-clause and exit
#%end

#%flag
#% key: d
#% description: Assign distance values to corridors instead of connection ids and weights
#%end

#%flag
#% key: r
#% description: Recalculate already computed corridors (default is only weight and summarize already existing corridor maps)
#%end

#%option
#% key: cores
#% type: integer
#% description: cores used for multithreading (1 means no multithreading)
#% required : no
#% answer : 1
#%end


import atexit
import os
import sys
import string

try:
    import resource
except ImportError:
    resource = None

import copy
from io import StringIO
import numpy as np
import grass.script as grass
import grass.script.task as task
from grass.script import vector as vect
from grass.pygrass.raster.history import History
from grass.pygrass.modules import Module, ParallelModuleQueue

# PY2/PY3 compat
if sys.version_info.major >= 3:
    unicode = str

### To do:
# Distinguish and remove temporary raster maps (single corridors)
# Prallelize aggregation (if meaningful)
# Fix history assignment for single corridors
# - grass.parse_command('v.support', map=edges, flags='g')[comments]
# - grass.parse_command('v.support', map=nodes, flags='g')[comments]
# Add description to history ("Generated by")
# Add User (creator) to history
# Add "flow_weighted" corridors (distance * distance_weight * pop_proxy)

# Add "flow map" (distance * distance_weight * pop_proxy) without any
#     constraints on max distance
# Maybe as new model r.connectivity.flow (that can be used on
#    r.connectivity.distance output directly; similar input as
#    r.connectivity.network (base, exponent, plotting, map generation,
#    plus where clause for edge selection))

# check if GRASS is running or not
if "GISBASE" not in os.environ:
    sys.exit("You must be in GRASS GIS to run this program")

# Define additional variables
# global TMP_PREFIX
# TMP_PREFIX = grass.tempname(12)


def write_raster_history(rastermap):
    """Write command history to raster map"""

    # grass.raster.raster_history('{}_patch_{}_cost_dist'.format(prefix, cat))
    cdhist = History(rastermap)
    cdhist.clear()
    cdhist.creator = os.environ["USER"]
    cdhist.write()
    # History object cannot modify description
    grass.run_command(
        "r.support",
        map=rastermap,
        description="Generated by r.connectivity.corridors",
        history=os.environ["CMDLINE"],
    )


def cleanup():
    """Remove temporary data"""

    # grass.run_command("g.remove", type=['vector', 'raster'],
    #                   pattern='{}*'.format(TMP_PREFIX), quiet=True)
    grass.del_temp_region()


def main():
    """Do the real work"""
    # Parse remaining variables
    network_map = options["input"]
    # network_mapset = network_map.split('@')[0]
    network = network_map.split("@")[1] if len(network_map.split("@")) > 1 else None
    suffix = options["suffix"]
    layer = options["layer"]
    corridor_tolerance = options["corridor_tolerance"]
    cores = options["cores"]
    where = None if options["where"] == "" else options["where"]
    weights = options["weights"].split(",")
    s_flag = flags["s"]
    d_flag = flags["d"]
    r_flag = flags["r"]

    ulimit = (512, 2048)  # Windows number of opened files (soft-limit, hard-limit)
    if resource:
        ulimit = resource.getrlimit(resource.RLIMIT_NOFILE)

    net_hist_str = (
        grass.read_command("v.info", map=network_map, flags="h")
        .split("\n")[0]
        .split(": ")[1]
    )

    dist_cmd_dict = task.cmdstring_to_tuple(net_hist_str)

    dist_prefix = dist_cmd_dict[1]["prefix"]
    # network_prefix = dist_cmd_dict[1]['prefix']

    # print(where)

    # in_vertices = dist_cmd_dict[1]['input']

    # Check if db-connection for edge map exists
    con = vect.vector_db(network_map)[int(layer)]
    if not con:
        grass.fatal(
            "Database connection for map {} \
                    is not defined for layer {}.".format(
                network, layer
            )
        )

    # Check if required columns exist and are of required type
    required_columns = ["con_id_u", "from_p", "to_p", "cd_u"]
    if weights:
        required_columns += weights

    in_columns = vect.vector_columns(network_map, layer=layer)

    missing_columns = np.setdiff1d(required_columns, in_columns.keys())

    if missing_columns:
        grass.fatal(
            "Cannot find the following required/requested \
                    column(s) {} in vector map \
                    {}.".format(
                ", ".join(missing_columns), network
            )
        )

    #
    weight_types = []
    # Check properly if column is numeric
    for col in required_columns:
        if in_columns[col]["type"] not in ["INTEGER", "DOUBLE PRECISION", "REAL"]:
            grass.fatal(
                "Column {} is of type {}. \
                         Only numeric types (integer, \
                         real or double precision) \
                         allowed!".format(
                    col, in_columns[col]["type"]
                )
            )

        if col in weights:
            weight_types.append(in_columns[col]["type"])

    # Extract necessary information on edges from attribute table of
    # edge map
    table_io = StringIO(
        unicode(
            grass.read_command(
                "v.db.select",
                flags="c",
                map=network_map,
                columns=required_columns,
                separator=",",
                where=where,
            )
        )
    )

    try:
        table_extract = np.genfromtxt(
            table_io, delimiter=",", dtype=None, names=required_columns
        )
    except:
        grass.fatal("No edges selected to compute corridors for...")

    # Output result of where-clause and exit (if requested)
    if s_flag:
        print(table_extract)
        # grass.message("con_id_u|from_p|to_p")
        # for fid in $selected_edges_ud:
        #    message_text = $(echo $table_extract | tr ' ' '\n' |
        # tr ',' ' ' | awk -v FID=$fid '{if($1==FID) print $1 "|" $2 "|"
        #  $3}' | head -n 1)
        #    grass.message(message_text)
        sys.exit(0)

    # Get unique identifiers for the selected undirected edges
    selected_patches = np.unique(
        np.append(table_extract["from_p"], table_extract["to_p"])
    )

    selected_edges = np.unique(table_extract["con_id_u"])

    # activate z-flag if more maps have to be aggregated than ulimit
    z_flag = None if len(selected_edges) < ulimit else "z"

    # Check if cost distance raster maps exist
    pattern = "{}_patch_*_cost_dist".format(dist_prefix)
    patchmaps = (
        grass.read_command("g.list", pattern=pattern, type="raster")
        .rstrip("\n")
        .split("\n")
    )

    for patch in selected_patches:
        # Check if cost distance raster maps exist
        patchmap = "{}_patch_{}_cost_dist".format(dist_prefix, patch)
        if patchmap not in patchmaps:
            grass.fatal("Cannot find raster map {}.".format(patchmap))

    # Create mapcalculator expressions for cost distance corridors,
    # assigning distance values
    corridormaps = {}
    if d_flag:
        pattern = "{}_corridor_*_cost_dist".format(dist_prefix)
        corridor_base = "dist"
    else:
        pattern = "{}_corridor_[0-9]+$".format(dist_prefix)
        corridor_base = "id"

    corridormaps[corridor_base] = (
        grass.read_command("g.list", flags="e", pattern=pattern, type="raster")
        .rstrip("\n")
        .split("\n")
    )
    for weight in weights:
        pattern = "{}_corridor_[0-9]+_{}".format(dist_prefix, weight)
        corridormaps[weight] = (
            grass.read_command("g.list", flags="e", pattern=pattern, type="raster")
            .rstrip("\n")
            .split("\n")
        )

    # Setup GRASS modules for raster processing
    mapcalc = Module("r.mapcalc", quiet=True, run_=False)
    reclass = Module("r.reclass", rules="-", quiet=True, run_=False)
    recode = Module("r.recode", rules="-", quiet=True, run_=False)

    # Setup parallel module queue if parallel processing is requested
    # print(weight_types)
    if cores > 1:
        mapcalc_queue = ParallelModuleQueue(nprocs=cores)

        if "INTEGER" in weight_types:
            reclass_queue = ParallelModuleQueue(nprocs=cores)

        if "REAL" in weight_types or "DOUBLE PRECISION" in weight_types:
            recode_queue = ParallelModuleQueue(nprocs=cores)

    corridor_list = []
    for edge_id in selected_edges:
        edge = table_extract[table_extract["con_id_u"] == edge_id][0]
        # print(e.dtype.names)
        if d_flag:
            corridor = "{}_corridor_{}_cost_dist".format(dist_prefix, edge_id)
            # corridor_list.append(corridor)
            mc_expression = "{prefix}_corridor_{CON_ID}_cost_dist=if( \
            ({prefix}_patch_{FROM_P}_cost_dist+ \
            {prefix}_patch_{TO_P}_cost_dist) - \
            (({prefix}_patch_{FROM_P}_cost_dist+ \
            {prefix}_patch_{TO_P}_cost_dist) * \
            {cor_tolerance}/100.0)<= \
            ({prefix}_patch_{FROM_P}_cost_dist + \
            {prefix}_patch_{TO_P}_cost_dist), \
            ({prefix}_patch_{FROM_P}_cost_dist+ \
            {prefix}_patch_{TO_P}_cost_dist), \
            null())".format(
                prefix=dist_prefix,
                CON_ID=edge["con_id_u"],
                FROM_P=edge["from_p"],
                TO_P=edge["to_p"],
                cor_tolerance=corridor_tolerance,
            )
        else:
            corridor = "{}_corridor_{}".format(dist_prefix, edge["con_id_u"])
            # corridor_list.append(corridor)
            # Create mapcalculator expressions for cost distance
            # corridors, assigning connection IDs for reclassification
            mc_expression = "{prefix}_corridor_{CON_ID}=if( \
            ({prefix}_patch_{FROM_P}_cost_dist+ \
            {prefix}_patch_{TO_P}_cost_dist)- \
            (({prefix}_patch_{FROM_P}_cost_dist+ \
            {prefix}_patch_{TO_P}_cost_dist)* \
            {cor_tolerance}/100.0)<={CD}, \
            {CON_ID}, null())".format(
                prefix=dist_prefix,
                CON_ID=edge["con_id_u"],
                FROM_P=edge["from_p"],
                TO_P=edge["to_p"],
                CD=edge["cd_u"],
                cor_tolerance=corridor_tolerance,
            )

        corridor_list.append(corridor)
        # print(corridor)
        # print(corridormaps)

        if r_flag or corridor not in corridormaps[corridor_base]:
            new_mapcalc = copy.deepcopy(mapcalc)

            if cores > 1:
                calc = new_mapcalc(expression=mc_expression)
                mapcalc_queue.put(calc)
            else:
                calc = new_mapcalc(expression=mc_expression, region="intersect")
                calc.run()

        for weight in weights:
            if r_flag or corridor not in corridormaps[weight]:
                in_map = corridor
                out_map = "{}_{}".format(in_map, weight)
                if in_columns[weight]["type"] == "INTEGER":
                    new_reclass = copy.deepcopy(reclass)
                    reclass_rule = "{} = {}".format(edge["con_id_u"], edge[weight])
                    rcl = new_reclass(input=in_map, output=out_map, stdin_=reclass_rule)

                    if cores > 1:
                        reclass_queue.put(rcl)
                    else:
                        rcl.run()

                if in_columns[weight]["type"] in ["REAL", "DOUBLE PRECISION"]:
                    new_recode = copy.deepcopy(recode)
                    recode_rule = "{0}:{0}:{1}:{1}".format(
                        edge["con_id_u"], edge[weight]
                    )
                    rco = new_recode(input=in_map, output=out_map, stdin_=recode_rule)
                    if cores > 1:
                        recode_queue.put(rco)
                    else:
                        rco.run()

    if cores > 1:
        mapcalc_queue.wait()
        if "INTEGER" in weight_types:
            reclass_queue.wait()
        if "REAL" in weight_types or "DOUBLE PRECISION" in weight_types:
            recode_queue.wait()

    grass.verbose("Aggregating corridor maps...")

    if d_flag:
        grass.run_command(
            "r.series",
            flags=z_flag,
            quiet=True,
            input=",".join(corridor_list),
            output="{}_corridors_min_cost_dist_{}".format(dist_prefix, suffix),
            method="minimum",
        )
    else:
        # Summarize corridors
        if not weights:
            print(",".join(corridor_list))
            output_map = "{}_corridors_count_{}".format(dist_prefix, suffix)
            grass.run_command(
                "r.series",
                flags=z_flag,
                quiet=True,
                input=",".join(corridor_list),
                output=output_map,
                method="count",
            )
            write_raster_history(output_map)

        else:
            # Weight corridors according to user requested weights
            for weight in weights:
                # Generate corridor map list
                corridor_map_list = (cm + "_{}".format(weight) for cm in corridor_list)
                output_map = "{}_corridors_{}_sum_{}".format(
                    dist_prefix, weight, suffix
                )
                # Summarize corridors using r.series
                grass.run_command(
                    "r.series",
                    flags=z_flag,
                    quiet=True,
                    input=corridor_map_list,
                    output=output_map,
                    method="sum",
                )
                write_raster_history(output_map)


if __name__ == "__main__":
    options, flags = grass.parser()
    atexit.register(cleanup)
    sys.exit(main())
