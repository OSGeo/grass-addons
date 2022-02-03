#!/usr/bin/env python
############################################################################
#
# MODULE:       v.stream.inbasin
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Build a drainage basin from the subwatersheds of a river
#               network, based on the structure of the network.
#
# COPYRIGHT:    (c) 2016 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from v.stream.network

# More information
# Started 14 October 2016

# %module
# % description: Subset a stream network into just one of its basins
# % keyword: vector
# % keyword: stream network
# % keyword: basins
# % keyword: hydrology
# % keyword: geomorphology
# %end

# %option G_OPT_V_INPUT
# %  key: input_streams
# %  label: Stream network
# %  required: yes
# %end

# %option G_OPT_V_INPUT
# %  key: input_basins
# %  label: Subbasins built alongside stream network
# %  required: no
# %end

# %option G_OPT_R_INPUT
# %  key: draindir
# %  label: Drainage directions (needed if exact coordinates used)
# %  required: no
# %end

# %option
# %  key: cat
# %  label: Farthest downstream segment category
# %  required: no
# %  guidependency: layer,column
# %end

# %option
# %  key: x_outlet
# %  label: Approx. pour point x/Easting: will find closest segment
# %  required: no
# %  guidependency: layer,column
# %end

# %option
# %  key: y_outlet
# %  label: Approx. pour point y/Northing: will find closest segment
# %  required: no
# %  guidependency: layer,column
# %end

# %option G_OPT_V_OUTPUT
# %  key: output_basin
# %  label: Vector output drainage basin
# %  required: no
# %end

# %option G_OPT_V_OUTPUT
# %  key: output_streams
# %  label: Streams within vector output drainage basin
# %  required: no
# %end

# %option G_OPT_V_OUTPUT
# %  key: output_pour_point
# %  label: Basin outlet
# %  required: no
# %end

# %flag
# %  key: s
# %  description: Snap provided coordinates to nearest segment endpoint
# %  guisection: Settings
# %end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np

# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript
from grass.pygrass.vector.geometry import Point

###############
# MAIN MODULE #
###############


def find_upstream_segments(cats, tostream, cat):
    """
    Find segments immediately upstream of the given one
    """
    pass


def main():
    """
    Links each river segment to the next downstream segment in a tributary
    network by referencing its category (cat) number in a new column. "0"
    means that the river exits the map.
    """

    options, flags = gscript.parser()

    streams = options["input_streams"]
    basins = options["input_basins"]
    downstream_cat = options["cat"]
    x_outlet = float(options["x_outlet"])
    y_outlet = float(options["y_outlet"])
    output_basins = options["output_basin"]
    output_streams = options["output_streams"]
    output_pour_point = options["output_pour_point"]
    draindir = options["draindir"]
    snapflag = flags["s"]

    # print options
    # print flags

    # Check that either x,y or cat are set
    if (downstream_cat != "") or ((x_outlet != "") and (y_outlet != "")):
        pass
    else:
        gscript.fatal('You must set either "cat" or "x_outlet" and "y_outlet".')

    # NEED TO ADD IF-STATEMENT HERE TO AVOID AUTOMATIC OVERWRITING!!!!!!!!!!!
    if snapflag or (downstream_cat != ""):
        if downstream_cat == "":
            # Need to find outlet pour point -- start by creating a point at this
            # location to use with v.distance
            try:
                v.db_droptable(table="tmp", flags="f")
            except:
                pass
            tmp = vector.Vector("tmp")
            _cols = [
                (u"cat", "INTEGER PRIMARY KEY"),
                (u"x", "DOUBLE PRECISION"),
                (u"y", "DOUBLE PRECISION"),
                (u"strcat", "DOUBLE PRECISION"),
            ]
            tmp.open("w", tab_name="tmp", tab_cols=_cols)
            point0 = Point(x_outlet, y_outlet)
            tmp.write(
                point0,
                cat=1,
                attrs=(str(x_outlet), str(y_outlet), 0),
            )
            tmp.table.conn.commit()
            tmp.build()
            tmp.close()
            # Now v.distance
            gscript.run_command(
                "v.distance", from_="tmp", to=streams, upload="cat", column="strcat"
            )
            # v.distance(_from_='tmp', to=streams, upload='cat', column='strcat')
            downstream_cat = gscript.vector_db_select(map="tmp", columns="strcat")
            downstream_cat = int(downstream_cat["values"].values()[0][0])

        # Attributes of streams
        colNames = np.array(vector_db_select(streams)["columns"])
        colValues = np.array(vector_db_select(streams)["values"].values())
        tostream = colValues[:, colNames == "tostream"].astype(int).squeeze()
        cats = colValues[:, colNames == "cat"].astype(int).squeeze()  # = "fromstream"

        # Find network
        basincats = [downstream_cat]  # start here
        most_upstream_cats = [
            downstream_cat
        ]  # all of those for which new cats must be sought
        while True:
            if len(most_upstream_cats) == 0:
                break
            tmp = list(most_upstream_cats)  # copy to a temp file: old values
            most_upstream_cats = []  # Ready to accept new values
            for ucat in tmp:
                most_upstream_cats += list(cats[tostream == int(ucat)])
                basincats += most_upstream_cats

        basincats = list(set(list(basincats)))

        basincats_str = ",".join(map(str, basincats))

        # Many basins out -- need to use overwrite flag in future!
        # SQL_OR = 'rnum = ' + ' OR rnum = '.join(map(str, basincats))
        # SQL_OR = 'cat = ' + ' OR cat = '.join(map(str, basincats))
        SQL_LIST = "cat IN (" + ", ".join(map(str, basincats)) + ")"
        if len(basins) > 0:
            v.extract(
                input=basins,
                output=output_basins,
                where=SQL_LIST,
                overwrite=gscript.overwrite(),
                quiet=True,
            )
        if len(streams) > 0:
            v.extract(
                input=streams,
                output=output_streams,
                cats=basincats_str,
                overwrite=gscript.overwrite(),
                quiet=True,
            )

    else:
        # Have coordinates and will limit the area that way.
        r.water_outlet(
            input=draindir,
            output="tmp",
            coordinates=(x_outlet, y_outlet),
            overwrite=True,
        )
        r.to_vect(input="tmp", output="tmp", type="area", overwrite=True)
        v.clip(input=basins, clip="tmp", output=output_basins, overwrite=True)
        basincats = gscript.vector_db_select("basins_inbasin").values()[0].keys()
        basincats_str = ",".join(map(str, basincats))
        if len(streams) > 0:
            v.extract(
                input=streams,
                output=output_streams,
                cats=basincats_str,
                overwrite=gscript.overwrite(),
                quiet=True,
            )

    # If we want to output the pour point location
    if len(output_pour_point) > 0:
        # NEED TO ADD IF-STATEMENT HERE TO AVOID AUTOMATIC OVERWRITING!!!!!!!!!!!
        try:
            v.db_droptable(table=output_pour_point, flags="f")
        except:
            pass
        if snapflag or (downstream_cat != ""):
            _pp = gscript.vector_db_select(
                map=streams, columns="x2,y2", where="cat=" + str(downstream_cat)
            )
            _xy = np.squeeze(_pp["values"].values())
            _x = float(_xy[0])
            _y = float(_xy[1])
        else:
            _x = x_outlet
            _y = y_outlet
        pptmp = vector.Vector(output_pour_point)
        _cols = [
            (u"cat", "INTEGER PRIMARY KEY"),
            (u"x", "DOUBLE PRECISION"),
            (u"y", "DOUBLE PRECISION"),
        ]
        pptmp.open("w", tab_name=output_pour_point, tab_cols=_cols)
        point0 = Point(_x, _y)
        pptmp.write(
            point0,
            cat=1,
            attrs=(str(_x), str(_y)),
        )
        pptmp.table.conn.commit()
        pptmp.build()
        pptmp.close()


if __name__ == "__main__":
    main()
