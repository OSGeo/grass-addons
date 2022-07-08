#!/usr/bin/env python

############################################################################
#
# MODULE:       v.what.strds.timestamp
# AUTHOR(S):    Stefan Blumentrath, NINA, based on
#               v.what.strds by Luca delucchi
#               Written for the IRSAE GIS course 2018 in Oslo
#
# PURPOSE:      Uploads space time raster dataset values at positions of vector points to the table
# COPYRIGHT:    (C) 2018 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (version 2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# %module
# % description: Uploads space time raster dataset values to the attribute table at positions of vector points in space and time.
# % keyword: vector
# % keyword: temporal
# % keyword: sampling
# % keyword: position
# % keyword: querying
# % keyword: attribute table
# % keyword: timestamp
# % keyword: time
# %end

# %option G_OPT_V_INPUT
# %end

# %option G_OPT_V_FIELD
# % required: yes
# % answer: 1
# %end

# %option G_OPT_DB_COLUMN
# % key: timestamp_column
# % required: yes
# % label: Column of input vector map containing time stamps for temoral sampling of STRDS
# %end

# %option G_OPT_DB_COLUMN
# % key: column
# % required: yes
# % label: Column of input vector map to which raster values are written
# % description: Column will be added if it does not exists or updated otherwise
# %end

# %option G_OPT_DB_WHERE
# % label: Where-clause for filtering points in input vector map used for sampling
# %end

# %option G_OPT_STRDS_INPUTS
# % key: strds
# %end

# %option G_OPT_T_WHERE
# % key: t_where
# % description: Temporal where-clause for selecting a subset of raster maps from STRDS for sampling (Default: The temporal bounding box of the input vector points)
# %end

# %flag
# % key: i
# % label: Interpolate raster values from the four nearest pixels
# %end

"""
To do:
- implement usage of temporal envelope of vector points
- implement relative temporal type
"""
import os

try:
    from subprocess import DEVNULL  # Python 3.
except ImportError:
    DEVNULL = open(os.devnull, "wb")
import grass.script as grass

# from grass.exceptions import CalledModuleError
import grass.temporal as tgis

# from grass.pygrass.utils import copy as gcopy
# from grass.pygrass.messages import Messenger
from grass.pygrass.modules import Module

# i18N
import gettext

gettext.install("grassmods", os.path.join(os.getenv("GISBASE"), "locale"))


def sample_relative(input, layer, timestamp_column, column, t_raster, where, i_flag):
    """Point sampling in STRDS with relative temporal type
    Not implemented yet.
    """
    start = t_raster["start_time"]
    end = t_raster["end_time"]
    raster_map = "{}@{}".format(t_raster["name"], t_raster["mapset"])
    where += """(julianday({0}) >= date('{1}') AND \
                julianday({0}) < date('{2}'))""".format(
        timestamp_column, start, end
    )


def sample_absolute(input, layer, timestamp_column, column, t_raster, where, i_flag):
    """Point sampling in STRDS with absolute temporal type"""
    start = t_raster["start_time"]
    end = t_raster["end_time"]
    raster_map = "{}@{}".format(t_raster["name"], t_raster["mapset"])
    where += """({0} >= date('{1}') AND \
                {0} < date('{2}'))""".format(
        timestamp_column, start, end
    )

    grass.verbose(_("Sampling points between {} and {}".format(start, end)))

    # If only one core is used, processing can be faster if computational region is temporarily moved
    # to where datapoints are (e.g. in case of tracking data)
    # Move computational region temporarily to where points are in
    # in space and time
    treg = grass.parse_command(
        "v.db.select", flags="r", map=input, where=where, quiet=True
    )  # stderr=subproess.PIPE,

    if len(set(treg.values())) > 1:
        grass.use_temp_region()
        grass.run_command(
            "g.region",
            n=treg["n"],
            s=treg["s"],
            e=treg["e"],
            w=treg["w"],
            align=raster_map,
        )

        # Sample spatio-temporally matching points and raster map
        rast_what = Module(
            "v.what.rast",
            map=input,
            layer=layer,
            column=column,
            raster=raster_map,
            where=where,
            stderr_=DEVNULL,
            run_=False,
            quiet=True,
        )
        rast_what.flags.i = i_flag
        rast_what.run()


def main():
    # Get the options
    input = options["input"]
    timestamp_column = options["timestamp_column"]
    columns = options["column"]
    layer = options["layer"]
    where = options["where"]
    strds = options["strds"]
    tempwhere = options["t_where"]
    i_flag = flags["i"]

    if where == "" or where == " " or where == "\n":
        where = None

    # overwrite = grass.overwrite()

    # Set verbosity level
    # quiet = True
    # if grass.verbosity() > 2:
    #     quiet = False

    # Check DB connection for input vector map
    dbcon = grass.vector_layer_db(input, layer)
    # Check the number of sample strds and the number of columns
    strds_names = strds.split(",")
    column_names = columns.split(",")
    if not len(column_names) == len(strds_names):
        grass.fatal(_("Number of columns and number of STRDS does not match."))

    # Check type of timestamp column
    cols = grass.vector_columns(input, layer=layer)
    if timestamp_column not in cols.keys():
        grass.fatal(
            _(
                "Could not find column {} \
                    in table connected to vector map {} \
                    at layer {}".format(
                    timestamp_column, input, layer
                )
            )
        )
    if cols[timestamp_column]["type"] != "DATE":
        if dbcon["driver"] != "sqlite":
            # Note that SQLite does not have a DATE datatype and
            # and an index does not significantly speedup the process
            # (at least not with a couple of 100 points)
            grass.warning(
                _(
                    "Timestamp column is of type {}. \
                            It is recommended to use DATE type with an index. \
                            ".format(
                        cols[timestamp_column]["type"]
                    )
                )
            )

    # Make sure the temporal database exists
    tgis.init()
    # We need a database interface
    dbif = tgis.SQLDatabaseInterfaceConnection()
    dbif.connect()

    # Limit temporal extent to extent of points if no tempwhere is given
    if not tempwhere:
        extent = []
        for stat in ("min", "max"):
            tsql = "SELECT {}({}) FROM {}".format(
                stat, timestamp_column, dbcon["table"]
            )
            extent.append(grass.read_command("db.select", flags="c", sql=tsql))

        grass.verbose(
            _(
                "Temporal extent of vector points map is \
                      {} to {}".format(
                    extent[0], extent[1]
                )
            )
        )
    else:
        tempwhere = "({}) AND ".format(tempwhere)

    # Loop over STRDS
    counter = 0
    for strds_name in strds_names:

        cur_strds = tgis.open_old_stds(strds_name, "strds", dbif)

        # skip current STRDS if no map is registered in it
        if cur_strds.metadata.get_number_of_maps() is None:
            grass.warning(
                _(
                    "Space time raster dataset {} does not contain any registered "
                    "map. It is being skipped.".format(cur_strds.get_id())
                )
            )
            counter += 1
            continue

        granu = cur_strds.get_granularity()
        start_time = tgis.datetime_math.check_datetime_string(extent[0])
        start_gran = tgis.datetime_math.adjust_datetime_to_granularity(
            start_time, granu
        ).isoformat()
        tempwhere += "(end_time > '{}' and start_time <= '{}')".format(
            start_gran, extent[1]
        )  # needs to be set properly

        # Get info on registered maps in STRDS
        rows = cur_strds.get_registered_maps(
            "name,mapset,start_time,end_time", tempwhere, "start_time", dbif
        )

        # Check temporal type and
        # define sampling function to use
        # becomes relevant when temporal type relative gets implemented
        if cur_strds.is_time_relative():
            grass.fatal(
                _("Sorry, STRDS of relative temporal type is not (yet) supported")
            )
            sample = sample_relative
        else:
            sample = sample_absolute

        # Check if there are raster maps to sample from that fullfill
        # temporal conditions
        if not rows and tempwhere:
            dbif.close()
            grass.fatal(
                _(
                    "No maps selected from Space time raster dataset "
                    "{}".format(cur_strds.get_id())
                )
            )

        # Include temporal condition into where clause
        where_clause = "({}) AND ".format(where) if where else ""

        # Loop over registered maps in STRDS
        row_number = 0
        for row in rows:
            # If r.what had a where option, r.what could be used to
            # collect raster values (without interpolation)
            # in a ParallelModuleQueue to collect values using multiple
            # cores and then upload results in one operation

            sample(
                input,
                layer,
                timestamp_column,
                column_names[counter],
                row,
                where_clause,
                i_flag,
            )

            row_number += 1
            grass.percent(row_number, len(rows), 3)
        counter = counter + 1

    dbif.close()
    grass.vector_history(input)


if __name__ == "__main__":
    options, flags = grass.parser()
    main()
