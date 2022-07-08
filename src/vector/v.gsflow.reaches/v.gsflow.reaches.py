#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.reaches
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Build reaches (intersection of PRMS Segments and MODFLOW
#               grid cells) for the GSFLOW (all USGS models)
#
# COPYRIGHT:    (c) 2016-2017 Andrew Wickert
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################
#
# REQUIREMENTS:
#      -  uses inputs from r.stream.extract

# More information
# Started December 2016

# %module
# % description: Build stream "reaches" that link PRMS segments to MODFLOW cells
# % keyword: vector
# % keyword: stream network
# % keyword: hydrology
# % keyword: GSFLOW
# %end

# %option G_OPT_V_INPUT
# %  key: segment_input
# %  label: PRMS stream segments
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_INPUT
# %  key: grid_input
# %  label: MODFLOW grid
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_R_INPUT
# %  key: elevation
# %  label: DEM for slope along reaches
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  label: Reaches for GSFLOW
# %  required: yes
# %  guidependency: layer,column
# %end

# %option
# %  key: s_min
# %  type: double
# %  description: Minimum reach slope
# %  answer: 0.0001
# %  required: no
# %end

# %option
# %  key: h_stream
# %  type: double
# %  description: Stream channel depth (bank height) [m]
# %  answer: 1
# %  required: no
# %end

# %option
# %  key: upstream_easting_column_seg
# %  type: string
# %  description: Upstream easting (or x or lon) column name
# %  answer: x1
# %  required : no
# %end

# %option
# %  key: upstream_northing_column_seg
# %  type: string
# %  description: Upstream northing (or y or lat) column name
# %  answer: y1
# %  required : no
# %end

# %option
# %  key: downstream_easting_column_seg
# %  type: string
# %  description: Downstream easting (or x or lon) column name
# %  answer: x2
# %  required : no
# %end

# %option
# %  key: downstream_northing_column_seg
# %  type: string
# %  description: Downstream northing (or y or lat) column name
# %  answer: y2
# %  required : no
# %end

# %option
# %  key: tostream_cat_column_seg
# %  type: string
# %  description: Adjacent downstream segment cat (0 = offmap)
# %  answer: tostream
# %  required : no
# %end

# %option
# %  key: strthick
# %  type: double
# %  description: Streambed sediment thickness [m]
# %  answer: 1
# %  required : no
# %end

# %option
# %  key: strhc1
# %  type: double
# %  description: Streambed hydraulic conductivity [m/day]
# %  answer: 5
# %  required : no
# %end

# %option
# %  key: thts
# %  type: double
# %  description: theta_sat: Streambed saturated water content (i.e. porosity) [unitless]
# %  answer: 0.35
# %  required : no
# %end

# %option
# %  key: thti
# %  type: double
# %  description: Streambed initial water content [unitless]
# %  answer: 0.3
# %  required : no
# %end

# %option
# %  key: eps
# %  type: double
# %  description: Epsilon: streambed Brooks-Corey exponent [unitless]
# %  answer: 3.5
# %  required : no
# %end

# %option
# %  key: uhc
# %  type: double
# %  description: Streambed unsaturated zone saturated hydraulic conductivity [m/day]
# %  answer: 0.3
# %  required : no
# %end

# Default values strthick onwards from sagehen example

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np

# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript

###############
# MAIN MODULE #
###############


def main():
    """
    Builds river reaches for input to the USGS hydrologic model, GSFLOW.
    These reaches link the PRMS stream segments to the MODFLOW grid cells.
    """

    ##################
    # OPTION PARSING #
    ##################

    options, flags = gscript.parser()
    segments = options["segment_input"]
    grid = options["grid_input"]
    reaches = options["output"]
    elevation = options["elevation"]
    Smin = options["s_min"]
    h_stream = options["h_stream"]
    x1 = options["upstream_easting_column_seg"]
    y1 = options["upstream_northing_column_seg"]
    x2 = options["downstream_easting_column_seg"]
    y2 = options["downstream_northing_column_seg"]
    tostream = options["tostream_cat_column_seg"]
    # Hydraulic paramters
    STRTHICK = options["strthick"]
    STRHC1 = options["strhc1"]
    THTS = options["thts"]
    THTI = options["thti"]
    EPS = options["eps"]
    UHC = options["uhc"]
    # Build reach maps by overlaying segments on grid
    if len(gscript.find_file(segments, element="vector")["name"]) > 0:
        v.extract(
            input=segments,
            output="GSFLOW_TEMP__",
            type="line",
            quiet=True,
            overwrite=True,
        )
        v.overlay(
            ainput="GSFLOW_TEMP__",
            atype="line",
            binput=grid,
            output=reaches,
            operator="and",
            overwrite=gscript.overwrite(),
            quiet=True,
        )
        g.remove(type="vector", name="GSFLOW_TEMP__", quiet=True, flags="f")
    else:
        gscript.fatal('No vector file "' + segments + '" found.')

    # Start editing database table
    reachesTopo = VectorTopo(reaches)
    reachesTopo.open("rw")

    # Rename a,b columns
    reachesTopo.table.columns.rename("a_" + x1, "x1")
    reachesTopo.table.columns.rename("a_" + x2, "x2")
    reachesTopo.table.columns.rename("a_" + y1, "y1")
    reachesTopo.table.columns.rename("a_" + y2, "y2")
    reachesTopo.table.columns.rename("a_NSEG", "NSEG")
    reachesTopo.table.columns.rename("a_ISEG", "ISEG")
    reachesTopo.table.columns.rename("a_stream_type", "stream_type")
    reachesTopo.table.columns.rename("a_type_code", "type_code")
    reachesTopo.table.columns.rename("a_cat", "rnum_cat")
    reachesTopo.table.columns.rename("a_" + tostream, "tostream")
    reachesTopo.table.columns.rename("a_id", "segment_id")
    reachesTopo.table.columns.rename("a_OUTSEG", "OUTSEG")
    reachesTopo.table.columns.rename("b_row", "row")
    reachesTopo.table.columns.rename("b_col", "col")
    reachesTopo.table.columns.rename("b_id", "cell_id")

    # Drop unnecessary columns
    cols = reachesTopo.table.columns.names()
    for col in cols:
        if (col[:2] == "a_") or (col[:2] == "b_"):
            reachesTopo.table.columns.drop(col)

    # Add new columns to 'reaches'
    reachesTopo.table.columns.add("KRCH", "integer")
    reachesTopo.table.columns.add("IRCH", "integer")
    reachesTopo.table.columns.add("JRCH", "integer")
    reachesTopo.table.columns.add("IREACH", "integer")
    reachesTopo.table.columns.add("RCHLEN", "double precision")
    reachesTopo.table.columns.add("STRTOP", "double precision")
    reachesTopo.table.columns.add("SLOPE", "double precision")
    reachesTopo.table.columns.add("STRTHICK", "double precision")
    reachesTopo.table.columns.add("STRHC1", "double precision")
    reachesTopo.table.columns.add("THTS", "double precision")
    reachesTopo.table.columns.add("THTI", "double precision")
    reachesTopo.table.columns.add("EPS", "double precision")
    reachesTopo.table.columns.add("UHC", "double precision")
    reachesTopo.table.columns.add("xr1", "double precision")
    reachesTopo.table.columns.add("xr2", "double precision")
    reachesTopo.table.columns.add("yr1", "double precision")
    reachesTopo.table.columns.add("yr2", "double precision")

    # Commit columns before editing (necessary?)
    reachesTopo.table.conn.commit()
    reachesTopo.close()

    # Update some columns that can be done now
    reachesTopo.open("rw")
    colNames = np.array(gscript.vector_db_select(reaches, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(reaches, layer=1)["values"].values())
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()
    nseg = np.arange(1, len(cats) + 1)
    nseg_cats = []
    for i in range(len(cats)):
        nseg_cats.append((nseg[i], cats[i]))
    cur = reachesTopo.table.conn.cursor()
    # Hydrogeologic properties
    cur.execute("update " + reaches + " set STRTHICK=" + str(STRTHICK))
    cur.execute("update " + reaches + " set STRHC1=" + str(STRHC1))
    cur.execute("update " + reaches + " set THTS=" + str(THTS))
    cur.execute("update " + reaches + " set THTI=" + str(THTI))
    cur.execute("update " + reaches + " set EPS=" + str(EPS))
    cur.execute("update " + reaches + " set UHC=" + str(UHC))
    # Grid properties
    cur.execute("update " + reaches + " set KRCH=1")  # Top layer: unchangable
    cur.executemany("update " + reaches + " set IRCH=? where row=?", nseg_cats)
    cur.executemany("update " + reaches + " set JRCH=? where col=?", nseg_cats)
    reachesTopo.table.conn.commit()
    reachesTopo.close()
    v.to_db(map=reaches, columns="RCHLEN", option="length", quiet=True)

    # Still to go after these:
    # STRTOP (added with slope)
    # IREACH (whole next section dedicated to this)
    # SLOPE (need z_start and z_end)

    # Now, the light stuff is over: time to build the reach order
    v.to_db(map=reaches, option="start", columns="xr1,yr1")
    v.to_db(map=reaches, option="end", columns="xr2,yr2")

    # Now just sort by category, find which stream has the same xr1 and yr1 as
    # x1 and y1 (or a_x1, a_y1) and then find where its endpoint matches another
    # starting point and move down the line.
    # v.db.select reaches col=cat,a_id,xr1,xr2 where="a_x1 = xr1"

    # First, get the starting coordinates of each stream segment
    # and a set of river ID's (ordered from 1...N)
    colNames = np.array(gscript.vector_db_select(segments, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(segments, layer=1)["values"].values())
    number_of_segments = colValues.shape[0]
    segment_x1s = colValues[:, colNames == "x1"].astype(float).squeeze()
    segment_y1s = colValues[:, colNames == "y1"].astype(float).squeeze()
    segment_ids = colValues[:, colNames == "id"].astype(float).squeeze()

    # Then move back to the reaches map to produce the ordering
    colNames = np.array(gscript.vector_db_select(reaches, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(reaches, layer=1)["values"].values())
    reach_cats = colValues[:, colNames == "cat"].astype(int).squeeze()
    reach_x1s = colValues[:, colNames == "xr1"].astype(float).squeeze()
    reach_y1s = colValues[:, colNames == "yr1"].astype(float).squeeze()
    reach_x2s = colValues[:, colNames == "xr2"].astype(float).squeeze()
    reach_y2s = colValues[:, colNames == "yr2"].astype(float).squeeze()
    segment_ids__reach = colValues[:, colNames == "segment_id"].astype(float).squeeze()

    for segment_id in segment_ids:
        reach_order_cats = []
        downstream_directed = []
        ssel = segment_ids == segment_id
        rsel = segment_ids__reach == segment_id  # selector
        # Find first segment: x1y1 first here, but not necessarily later
        downstream_directed.append(1)
        _x_match = reach_x1s[rsel] == segment_x1s[ssel]
        _y_match = reach_y1s[rsel] == segment_y1s[ssel]
        _i_match = _x_match * _y_match
        x1y1 = True  # false if x2y2
        # Find cat
        _cat = int(reach_cats[rsel][_x_match * _y_match])
        reach_order_cats.append(_cat)
        # Get end of reach = start of next one
        reach_x_end = float(reach_x2s[reach_cats == _cat])
        reach_y_end = float(reach_y2s[reach_cats == _cat])
        while _i_match.any():
            _x_match = reach_x1s[rsel] == reach_x_end
            _y_match = reach_y1s[rsel] == reach_y_end
            _i_match = _x_match * _y_match
            if _i_match.any():
                _cat = int(reach_cats[rsel][_x_match * _y_match])
                reach_x_end = float(reach_x2s[reach_cats == _cat])
                reach_y_end = float(reach_y2s[reach_cats == _cat])
                reach_order_cats.append(_cat)
        _message = str(len(reach_order_cats)) + " " + str(len(reach_cats[rsel]))
        gscript.message(_message)

        # Reach order to database table
        reach_number__reach_order_cats = []
        for i in range(len(reach_order_cats)):
            reach_number__reach_order_cats.append((i + 1, reach_order_cats[i]))
        reachesTopo = VectorTopo(reaches)
        reachesTopo.open("rw")
        cur = reachesTopo.table.conn.cursor()
        cur.executemany(
            "update " + reaches + " set IREACH=? where cat=?",
            reach_number__reach_order_cats,
        )
        reachesTopo.table.conn.commit()
        reachesTopo.close()

    # TOP AND BOTTOM ARE OUT OF ORDER: SOME SEGS ARE BACKWARDS. UGH!!!!
    # NEED TO GET THEM IN ORDER TO GET THE Z VALUES AT START AND END

    # 2018.10.01: Updating this to use the computational region for the DEM
    g.region(raster=elevation)

    # Compute slope and starting elevations from the elevations at the start and
    # end of the reaches and the length of each reach]

    gscript.message("Obtaining elevation values from raster: may take time.")
    v.db_addcolumn(map=reaches, columns="zr1 double precision, zr2 double precision")
    zr1 = []
    zr2 = []
    for i in range(len(reach_cats)):
        _x = reach_x1s[i]
        _y = reach_y1s[i]
        # print _x, _y
        _z = float(
            gscript.parse_command(
                "r.what", map=elevation, coordinates=str(_x) + "," + str(_y)
            )
            .keys()[0]
            .split("|")[-1]
        )
        zr1.append(_z)
        _x = reach_x2s[i]
        _y = reach_y2s[i]
        _z = float(
            gscript.parse_command(
                "r.what", map=elevation, coordinates=str(_x) + "," + str(_y)
            )
            .keys()[0]
            .split("|")[-1]
        )
        zr2.append(_z)

    zr1_cats = []
    zr2_cats = []
    for i in range(len(reach_cats)):
        zr1_cats.append((zr1[i], reach_cats[i]))
        zr2_cats.append((zr2[i], reach_cats[i]))

    reachesTopo = VectorTopo(reaches)
    reachesTopo.open("rw")
    cur = reachesTopo.table.conn.cursor()
    cur.executemany("update " + reaches + " set zr1=? where cat=?", zr1_cats)
    cur.executemany("update " + reaches + " set zr2=? where cat=?", zr2_cats)
    reachesTopo.table.conn.commit()
    reachesTopo.close()

    # Use these to create slope -- backwards possible on DEM!
    v.db_update(map=reaches, column="SLOPE", value="(zr1 - zr2)/RCHLEN")
    v.db_update(map=reaches, column="SLOPE", value=Smin, where="SLOPE <= " + str(Smin))

    # srtm_local_filled_grid = srtm_local_filled @ 200m (i.e. current grid)
    #  resolution
    # r.to.vect in=srtm_local_filled_grid out=srtm_local_filled_grid col=z type=area --o#
    # NOT SURE IF IT IS BEST TO USE MEAN ELEVATION OR TOP ELEVATION!!!!!!!!!!!!!!!!!!!!!!!
    v.db_addcolumn(map=reaches, columns="z_topo_mean double precision")
    v.what_rast(
        map=reaches, raster=elevation, column="z_topo_mean"
    )  # , query_column='z')
    v.db_update(
        map=reaches, column="STRTOP", value="z_topo_mean -" + str(h_stream), quiet=True
    )


if __name__ == "__main__":
    main()
