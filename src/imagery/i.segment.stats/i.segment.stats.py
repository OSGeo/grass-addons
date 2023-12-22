#!/usr/bin/env python
############################################################################
#
# MODULE:       i.segment.stats
# AUTHOR:       Moritz Lennert
# PURPOSE:      Calculates statistics describing raster areas
#               (notably for segments resulting from i.segment)
#
# COPYRIGHT:    (c) 2015 Moritz Lennert, and the GRASS Development Team
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Calculates statistics describing raster areas.
# % keyword: imagery
# % keyword: segmentation
# % keyword: statistics
# % keyword: parallel
# %end
# %option G_OPT_R_MAP
# % label: Name for input raster map with areas
# % description: Raster map with areas (all pixels of an area have same id), such as the output of i.segment
# % required: yes
# %end
# %option G_OPT_R_INPUTS
# % key: rasters
# % description: Name of input raster maps for statistics
# % multiple: yes
# % required: no
# % guisection: Raster statistics
# %end
# %option
# % key: raster_statistics
# % type: string
# % label: Statistics to calculate for each input raster map
# % required: no
# % multiple: yes
# % options: min,max,range,mean,mean_of_abs,stddev,variance,coeff_var,sum,sum_abs,first_quart,median,third_quart,perc_90
# % answer: mean,stddev,sum
# % guisection: Raster statistics
# %end
# %rules
# % requires: raster_statistics,rasters
# %end
# %option
# % key: area_measures
# % type: string
# % label: Area measurements to include in the output
# % required: no
# % multiple: yes
# % options: area,perimeter,compact_circle,compact_square,fd,xcoords,ycoords
# % answer: area,perimeter,compact_circle,fd
# % guisection: Shape statistics
# %end
# %option G_OPT_F_OUTPUT
# % key: csvfile
# % description: Name for output CSV file containing statistics
# % required: no
# % guisection: Output
# %end
# %option G_OPT_F_SEP
# % guisection: Output
# %end
# %option G_OPT_V_OUTPUT
# % key: vectormap
# % description: Name for optional vector output map with statistics as attributes
# % required: no
# % guisection: Output
# %end
# %option
# % key: processes
# % type: integer
# % description: Number of processes to run in parallel (for multiple rasters)
# % required: no
# % answer: 1
# %end
# %rules
# % required: csvfile,vectormap
# %end
# %flag
# % key: r
# % description: Adjust region to input map
# %end
# %flag
# % key: n
# % description: Calculate neighborhood statistics
# %end
# %flag
# % key: s
# % description: Do not calculate any shape statistics
# % guisection: Shape statistics
# %end
# %flag
# % key: c
# % description: Do not check rasters for null cells
# %END


import os
import glob
import atexit
import collections
from math import sqrt
from functools import partial
from multiprocessing import Pool
from itertools import groupby
import grass.script as gscript


def cleanup():

    if temporary_vect:
        if gscript.find_file(temporary_vect, element="vector")["name"]:
            gscript.run_command(
                "g.remove", flags="f", type_="vector", name=temporary_vect, quiet=True
            )
        if gscript.db_table_exist(temporary_vect):
            gscript.run_command(
                "db.execute", sql="DROP TABLE %s" % temporary_vect, quiet=True
            )

    if insert_sql:
        os.remove(insert_sql)

    if stats_temp_file:
        os.remove(stats_temp_file)

    if rasters:
        for tempfile in glob.glob(stats_temp_file + ".*"):
            os.remove(tempfile)


# The following two functions come from
# https://en.wikipedia.org/wiki/Algorithms_for_calculating_variance#Welford%27s_Online_algorithm
def update(existingAggregate, newValue):
    (count, mean, M2) = existingAggregate
    count = count + 1
    delta = newValue - mean
    mean = mean + float(delta) / count
    delta2 = newValue - mean
    M2 = M2 + delta * delta2
    return (count, mean, M2)


def finalize(existingAggregate):
    (count, mean, M2) = existingAggregate
    (mean, stddev) = (mean, sqrt(float(M2) / count))
    if count < 2:
        return float("nan")
    else:
        return (mean, stddev)


def worker(segment_map, stat_temp_file, raster):

    rastername = raster.split("@")[0]
    rastername = rastername.replace(".", "_")
    temp_file = stat_temp_file + "." + rastername
    gscript.run_command(
        "r.univar",
        map_=raster,
        zones=segment_map,
        output=temp_file,
        flags="et",
        overwrite=True,
        quiet=True,
    )


def main():

    global insert_sql
    insert_sql = None
    global temporary_vect
    temporary_vect = None
    global stats_temp_file
    stats_temp_file = None

    segment_map = options["map"]
    csvfile = options["csvfile"] if options["csvfile"] else []
    vectormap = options["vectormap"] if options["vectormap"] else []
    global rasters
    rasters = options["rasters"].split(",") if options["rasters"] else []
    area_measures = (
        options["area_measures"].split(",")
        if (options["area_measures"] and not flags["s"])
        else []
    )
    neighborhood = True if flags["n"] else False
    if neighborhood:
        if not gscript.find_program("r.neighborhoodmatrix", "--help"):
            message = _("You need to install the addon r.neighborhoodmatrix to be able")
            message += _(" to calculate area measures.\n")
            message += _(
                " You can install the addon with 'g.extension r.neighborhoodmatrix'"
            )
            gscript.fatal(message)

    raster_statistics = (
        options["raster_statistics"].split(",") if options["raster_statistics"] else []
    )
    separator = gscript.separator(options["separator"])
    processes = int(options["processes"])

    output_header = ["cat"]
    output_dict = collections.defaultdict(list)

    raster_stat_dict = {
        "zone": 0,
        "min": 4,
        "third_quart": 16,
        "max": 5,
        "sum": 12,
        "null_cells": 3,
        "median": 15,
        "label": 1,
        "first_quart": 14,
        "range": 6,
        "mean_of_abs": 8,
        "stddev": 9,
        "non_null_cells": 2,
        "coeff_var": 11,
        "variance": 10,
        "sum_abs": 13,
        "perc_90": 17,
        "mean": 7,
    }

    geometry_stat_dict = {
        "cat": 0,
        "area": 1,
        "perimeter": 2,
        "compact_square": 3,
        "compact_circle": 4,
        "fd": 5,
        "xcoords": 6,
        "ycoords": 7,
    }

    if flags["r"]:
        gscript.use_temp_region()
        gscript.run_command("g.region", raster=segment_map)

    stats_temp_file = gscript.tempfile()
    if area_measures:
        gscript.message(_("Calculating geometry statistics..."))
        output_header += area_measures
        stat_indices = [geometry_stat_dict[x] for x in area_measures]
        gscript.run_command(
            "r.object.geometry",
            input_=segment_map,
            output=stats_temp_file,
            overwrite=True,
            quiet=True,
        )

        firstline = True
        with open(stats_temp_file, "r") as fin:
            for line in fin:
                if firstline:
                    firstline = False
                    continue
                values = line.rstrip().split("|")
                output_dict[values[0]] = [values[x] for x in stat_indices]

    if rasters:
        if not flags["c"]:
            gscript.message(_("Checking usability of raster maps..."))
            rasters_to_remove = []
            for raster in rasters:
                null_values_found = False
                if not gscript.find_file(raster, element="cell")["name"]:
                    gscript.message(_("Cannot find raster '%s'" % raster))
                    gscript.message(_("Removing this raster from list."))
                    rasters_to_remove.append(raster)
                    continue
                current_mapset = gscript.gisenv()["MAPSET"]
                if gscript.find_file("MASK", element="cell", mapset=current_mapset)[
                    "name"
                ]:

                    null_test = gscript.read_command(
                        "r.stats", flags="N", input_=["MASK", raster], quiet=True
                    ).splitlines()
                    if "1 *" in null_test:
                        null_values_found = True

                else:
                    raster_info = gscript.parse_command(
                        "r.univar", flags="g", map_=raster, quiet=True
                    )
                    if len(raster_info) == 0 or int(raster_info["null_cells"]) > 0:
                        null_values_found = True

                if null_values_found:
                    message = "Raster <%s> contains null values.\n" % raster
                    message += "This can lead to errors in the calculations.\n"
                    message += "Check region settings and raster extent.\n"
                    message += "Possibly fill null values of raster.\n"
                    message += "Removing this raster from list."
                    gscript.warning(message)
                    rasters_to_remove.append(raster)

            for raster in rasters_to_remove:
                rasters.remove(raster)

        if len(rasters) > 0:
            gscript.message(_("Calculating statistics for the following raster maps:"))
            gscript.message(",".join(rasters))
            if len(rasters) < processes:
                processes = len(rasters)
                gscript.message(
                    _(
                        "Only one process per raster. Reduced number of processes to %i."
                        % processes
                    )
                )

            stat_indices = [raster_stat_dict[x] for x in raster_statistics]
            pool = Pool(processes)
            func = partial(worker, segment_map, stats_temp_file)
            pool.map(func, rasters)
            pool.close()
            pool.join()

            for raster in rasters:
                rastername = raster.split("@")[0]
                rastername = rastername.replace(".", "_")
                temp_file = stats_temp_file + "." + rastername
                output_header += [rastername + "_" + x for x in raster_statistics]
                firstline = True
                with open(temp_file, "r") as fin:
                    for line in fin:
                        if firstline:
                            firstline = False
                            continue
                        values = line.rstrip().split("|")
                        output_dict[values[0]] = output_dict[values[0]] + [
                            values[x] for x in stat_indices
                        ]

    # Calculating neighborhood statistics if requested
    if neighborhood:

        gscript.message(_("Calculating neighborhood statistics..."))

        # Add neighbordhood statistics to headers
        original_nb_values = len(output_header) - 1
        new_headers = ["neighbors_count"]
        for i in range(1, len(output_header)):
            new_headers.append("%s_nbrmean" % output_header[i])
            new_headers.append("%s_nbrstddev" % output_header[i])

        output_header += new_headers

        # Get sorted neighborhood matrix
        nbr_matrix = sorted(
            [
                x.split("|")
                for x in gscript.read_command(
                    "r.neighborhoodmatrix", input_=segment_map, flags="d", quiet=True
                ).splitlines()
            ]
        )

        # Calculate mean and stddev of neighbor values for each variable in the
        # output_dict
        for key, group in groupby(nbr_matrix, lambda x: x[0]):
            d = {}
            for i in range(original_nb_values):
                d[i] = (0, 0, 0)
            nbrlist = [str(x[1]) for x in group]
            if len(nbrlist) > 1:
                for nbr in nbrlist:
                    for i in range(original_nb_values):
                        d[i] = update(d[i], float(output_dict[nbr][i]))
                output_dict[key] = output_dict[key] + [str(len(nbrlist))]
                output_dict[key] = output_dict[key] + [
                    str(i) for sub in [finalize(x) for x in d.values()] for i in sub
                ]
            else:
                newvalues = ["1"]
                nbr = nbrlist[0]
                for i in range(original_nb_values):
                    newvalues.append(output_dict[nbr][i])
                    newvalues.append("0")
                output_dict[key] = output_dict[key] + newvalues

    message = _("Some values could not be calculated for the objects below. ")
    message += _("These objects are thus not included in the results. ")
    message += _("HINT: Check some of the raster maps for null values ")
    message += _("and possibly fill these values with r.fillnulls.")
    error_objects = []

    if csvfile:
        with open(csvfile, "w") as f:
            f.write(separator.join(output_header) + "\n")
            for key in output_dict:
                if len(output_dict[key]) + 1 == len(output_header):
                    f.write(key + separator + separator.join(output_dict[key]) + "\n")
                else:
                    error_objects.append(key)
        f.close()

    if vectormap:
        gscript.message(_("Creating output vector map..."))
        temporary_vect = "segmstat_tmp_vect_%d" % os.getpid()
        gscript.run_command(
            "r.to.vect",
            input_=segment_map,
            output=temporary_vect,
            type_="area",
            flags="vt",
            overwrite=True,
            quiet=True,
        )

        insert_sql = gscript.tempfile()
        fsql = open(insert_sql, "w")
        fsql.write("BEGIN TRANSACTION;\n")
        if gscript.db_table_exist(temporary_vect):
            if gscript.overwrite():
                fsql.write("DROP TABLE %s;" % temporary_vect)
            else:
                gscript.fatal(
                    _("Table %s already exists. Use --o to overwrite" % temporary_vect)
                )
        create_statement = (
            "CREATE TABLE " + temporary_vect + " (cat int PRIMARY KEY);\n"
        )
        fsql.write(create_statement)
        for header in output_header[1:]:
            addcol_statement = "ALTER TABLE %s ADD COLUMN %s double precision;\n" % (
                temporary_vect,
                header,
            )
            fsql.write(addcol_statement)
        for key in output_dict:
            if len(output_dict[key]) + 1 == len(output_header):
                sql = "INSERT INTO %s VALUES (%s, %s);\n" % (
                    temporary_vect,
                    key,
                    ",".join(output_dict[key]),
                )
                sql = sql.replace("inf", "NULL")
                sql = sql.replace("nan", "NULL")
                fsql.write(sql)
            else:
                if not csvfile:
                    error_objects.append(key)

        fsql.write("END TRANSACTION;")
        fsql.close()

        gscript.run_command("db.execute", input=insert_sql, quiet=True)
        gscript.run_command(
            "v.db.connect", map_=temporary_vect, table=temporary_vect, quiet=True
        )
        gscript.run_command(
            "g.copy", vector="%s,%s" % (temporary_vect, vectormap), quiet=True
        )

    if error_objects:
        object_string = ", ".join(error_objects[:100])
        message += _(
            "\n\nObjects with errors (only first 100 are shown):\n%s" % object_string
        )
        gscript.message(message)


if __name__ == "__main__":
    options, flags = gscript.parser()
    atexit.register(cleanup)
    main()
