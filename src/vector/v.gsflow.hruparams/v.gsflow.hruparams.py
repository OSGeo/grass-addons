#!/usr/bin/env python
############################################################################
#
# MODULE:       v.gsflow.hruparams
#
# AUTHOR(S):    Andrew Wickert
#
# PURPOSE:      Set parameters for GSFLOW Hydrologic Response Units (HRUs)
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
#      -  uses inputs from v.stream.network
#      -  uses inputs from r.slope.aspect

# More information
# Started December 2016

# %module
# %  description: Set parameters for GSFLOW Hydrologic Response Units (HRUs)
# %  keyword: vector
# %  keyword: stream network
# %  keyword: hydrology
# %  keyword: GSFLOW
# %end

# %option G_OPT_R_INPUT
# %  key: elevation
# %  label: Elevation raster
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_R_INPUT
# %  key: cov_type
# %  label: land cover: rast or int: 0=bare soil; 1=grass; 2=shrub; 3=tree; 4=conif
# %  answer: 0
# %  required: no
# %  guidependency: layer,column
# %end

# %option G_OPT_R_INPUT
# %  key: soil_type
# %  label: soil: rast or int: 1=sand; 2=loam; 3=clay
# %  answer: 2
# %  required: no
# %  guidependency: layer,column
# %end

# %option G_OPT_V_INPUT
# %  key: input
# %  label: Sub-basins to become HRUs
# %  required: yes
# %  guidependency: layer,column
# %end

# %option G_OPT_V_OUTPUT
# %  key: output
# %  label: HRUs
# %  required: yes
# %  guidependency: layer,column
# %end

# %option
# %  key: slope
# %  type: string
# %  description: Slope [unitless]: r.slope.aspect format=percent zscale=0.01
# %  required: yes
# %end

# %option
# %  key: aspect
# %  type: string
# %  description: Aspect from r.slope.aspect
# %  required: yes
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
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector  # Change to "v"?
from grass.script import vector_db_select
from grass.pygrass.vector import Vector, VectorTopo
from grass.pygrass.vector.geometry import Point
from grass.pygrass.raster import RasterRow
from grass.pygrass import utils
from grass import script as gscript

################
# MAIN MODULES #
################


def create_iterator(vect):
    colNames = np.array(gscript.vector_db_select(vect, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(vect, layer=1)["values"].values())
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()
    _n = np.arange(1, len(cats) + 1)
    _n_cats = []
    for i in range(len(cats)):
        _n_cats.append((_n[i], cats[i]))
    return _n_cats


def main():
    """
    Adds GSFLOW parameters to a set of HRU sub-basins
    """

    ##################
    # OPTION PARSING #
    ##################

    options, flags = gscript.parser()
    basins = options["input"]
    HRU = options["output"]
    slope = options["slope"]
    aspect = options["aspect"]
    elevation = options["elevation"]
    land_cover = options["cov_type"]
    soil = options["soil_type"]

    ################################
    # CREATE HRUs FROM SUB-BASINS  #
    ################################

    g.copy(vector=(basins, HRU), overwrite=gscript.overwrite())

    ############################################
    # ATTRIBUTE COLUMNS (IN ORDER FROM MANUAL) #
    ############################################

    # HRU
    hru_columns = []
    # Self ID
    hru_columns.append("id integer")  # nhru
    # Basic Physical Attributes (Geometry)
    hru_columns.append("hru_area double precision")  # acres (!!!!)
    hru_columns.append("hru_area_m2 double precision")  # [not for GSFLOW: for me!]
    hru_columns.append("hru_aspect double precision")  # Mean aspect [degrees]
    hru_columns.append("hru_elev double precision")  # Mean elevation
    hru_columns.append("hru_lat double precision")  # Latitude of centroid
    hru_columns.append("hru_lon double precision")  # Longitude of centroid
    # unnecessary but why not?
    hru_columns.append("hru_slope double precision")  # Mean slope [percent]
    # Basic Physical Attributes (Other)
    # hru_columns.append('hru_type integer') # 0=inactive; 1=land; 2=lake; 3=swale; almost all will be 1
    # hru_columns.append('elev_units integer') # 0=feet; 1=meters. 0=default. I think I will set this to 1 by default.
    # Measured input
    hru_columns.append(
        "outlet_sta integer"
    )  # Index of streamflow station at basin outlet:
    # station number if it has one, 0 if not
    # Note that the below specify projections and note lat/lon; they really seem
    # to work for any projected coordinates, with _x, _y, in meters, and _xlong,
    # _ylat, in feet (i.e. they are just northing and easting). The meters and feet
    # are not just simple conversions, but actually are required for different
    # modules in the code, and are hence redundant but intentional.
    hru_columns.append("hru_x double precision")  # Easting [m]
    hru_columns.append("hru_xlong double precision")  # Easting [feet]
    hru_columns.append("hru_y double precision")  # Northing [m]
    hru_columns.append("hru_ylat double precision")  # Northing [feet]
    # Streamflow and lake routing
    hru_columns.append(
        "K_coef double precision"
    )  # Travel time of flood wave to next downstream segment;
    # this is the Muskingum storage coefficient
    # 1.0 for reservoirs, diversions, and segments flowing
    # out of the basin
    hru_columns.append("x_coef double precision")  # Amount of attenuation of flow wave;
    # this is the Muskingum routing weighting factor
    # range: 0.0--0.5; default 0.2
    # 0 for all segments flowing out of the basin
    hru_columns.append(
        "hru_segment integer"
    )  # ID of stream segment to which flow will be routed
    # this is for non-cascade routing (flow goes directly
    # from HRU to stream segment)
    hru_columns.append(
        "obsin_segment integer"
    )  # Index of measured streamflow station that replaces
    # inflow to a segment
    hru_columns.append(
        "cov_type integer"
    )  # 0=bare soil;1=grasses; 2=shrubs; 3=trees; 4=coniferous
    hru_columns.append("soil_type integer")  # 1=sand; 2=loam; 3=clay

    # Create strings
    hru_columns = ",".join(hru_columns)

    # Add columns to tables
    v.db_addcolumn(map=HRU, columns=hru_columns, quiet=True)

    ###########################
    # UPDATE DATABASE ENTRIES #
    ###########################

    colNames = np.array(gscript.vector_db_select(HRU, layer=1)["columns"])
    colValues = np.array(gscript.vector_db_select(HRU, layer=1)["values"].values())
    number_of_hrus = colValues.shape[0]
    cats = colValues[:, colNames == "cat"].astype(int).squeeze()
    rnums = colValues[:, colNames == "rnum"].astype(int).squeeze()

    nhru = np.arange(1, number_of_hrus + 1)
    nhrut = []
    for i in range(len(nhru)):
        nhrut.append((nhru[i], cats[i]))
    # Access the HRUs
    hru = VectorTopo(HRU)
    # Open the map with topology:
    hru.open("rw")
    # Create a cursor
    cur = hru.table.conn.cursor()
    # Use it to loop across the table
    cur.executemany("update " + HRU + " set id=? where cat=?", nhrut)
    # Commit changes to the table
    hru.table.conn.commit()
    # Close the table
    hru.close()

    """
    # Do the same for basins <-------------- DO THIS OR SIMPLY HAVE HRUs OVERLAIN WITH GRID CELLS? IN THIS CASE, RMV AREA ADDITION TO GRAVRES
    v.db_addcolumn(map=basins, columns='id int', quiet=True)
    basins = VectorTopo(basins)
    basins.open('rw')
    cur = basins.table.conn.cursor()
    cur.executemany("update basins set id=? where cat=?", nhrut)
    basins.table.conn.commit()
    basins.close()
    """

    # if you want to append to table
    # cur.executemany("update HRU(id) values(?)", nhrut) # "insert into" will add rows

    # hru_columns.append('hru_area double precision')
    # Acres b/c USGS
    v.to_db(map=HRU, option="area", columns="hru_area", units="acres", quiet=True)
    v.to_db(map=HRU, option="area", columns="hru_area_m2", units="meters", quiet=True)

    # GET MEAN VALUES FOR THESE NEXT ONES, ACROSS THE BASIN

    # SLOPE (and aspect)
    #####################
    v.rast_stats(
        map=HRU,
        raster=slope,
        method="average",
        column_prefix="tmp",
        flags="c",
        quiet=True,
    )
    v.db_update(map=HRU, column="hru_slope", query_column="tmp_average", quiet=True)

    # ASPECT
    #########
    v.db_dropcolumn(map=HRU, columns="tmp_average", quiet=True)
    # Dealing with conversion from degrees (no good average) to something I can
    # average -- x- and y-vectors
    # Geographic coordinates, so sin=x, cos=y.... not that it matters so long
    # as I am consistent in how I return to degrees
    r.mapcalc(
        "aspect_x = sin(" + aspect + ")", overwrite=gscript.overwrite(), quiet=True
    )
    r.mapcalc(
        "aspect_y = cos(" + aspect + ")", overwrite=gscript.overwrite(), quiet=True
    )
    # grass.run_command('v.db.addcolumn', map=HRU, columns='aspect_x_sum double precision, aspect_y_sum double precision, ncells_in_hru integer')
    v.rast_stats(
        map=HRU,
        raster="aspect_x",
        method="sum",
        column_prefix="aspect_x",
        flags="c",
        quiet=True,
    )
    v.rast_stats(
        map=HRU,
        raster="aspect_y",
        method="sum",
        column_prefix="aspect_y",
        flags="c",
        quiet=True,
    )
    hru = VectorTopo(HRU)
    hru.open("rw")
    cur = hru.table.conn.cursor()
    cur.execute("SELECT cat,aspect_x_sum,aspect_y_sum FROM %s" % hru.name)
    _arr = np.array(cur.fetchall()).astype(float)
    _cat = _arr[:, 0]
    _aspect_x_sum = _arr[:, 1]
    _aspect_y_sum = _arr[:, 2]
    aspect_angle = np.arctan2(_aspect_y_sum, _aspect_x_sum) * 180.0 / np.pi
    aspect_angle[aspect_angle < 0] += 360  # all positive
    aspect_angle_cat = np.vstack((aspect_angle, _cat)).transpose()
    cur.executemany("update " + HRU + " set hru_aspect=? where cat=?", aspect_angle_cat)
    hru.table.conn.commit()
    hru.close()

    # ELEVATION
    ############
    v.rast_stats(
        map=HRU,
        raster=elevation,
        method="average",
        column_prefix="tmp",
        flags="c",
        quiet=True,
    )
    v.db_update(map=HRU, column="hru_elev", query_column="tmp_average", quiet=True)
    v.db_dropcolumn(map=HRU, columns="tmp_average", quiet=True)

    # CENTROIDS
    ############

    # get x,y of centroid -- but have areas not in database table, that do have
    # centroids, and having a hard time finding a good way to get rid of them!
    # They have duplicate category values!
    # Perhaps these are little dangles on the edges of the vectorization where
    # the raster value was the same but pinched out into 1-a few cells?
    # From looking at map, lots of extra centroids on area boundaries, and removing
    # small areas (though threshold hard to guess) gets rid of these

    hru = VectorTopo(HRU)
    hru.open("rw")
    hru_cats = []
    hru_coords = []
    for hru_i in hru:
        if isinstance(hru_i, vector.geometry.Centroid):
            hru_cats.append(hru_i.cat)
            hru_coords.append(hru_i.coords())
    hru_cats = np.array(hru_cats)
    hru_coords = np.array(hru_coords)
    hru.rewind()

    hru_area_ids = []
    for coor in hru_coords:
        _area = hru.find_by_point.area(Point(coor[0], coor[1]))
        hru_area_ids.append(_area)
    hru_area_ids = np.array(hru_area_ids)
    hru.rewind()

    hru_areas = []
    for _area_id in hru_area_ids:
        hru_areas.append(_area_id.area())
    hru_areas = np.array(hru_areas)
    hru.rewind()

    allcats = sorted(list(set(list(hru_cats))))

    # Now create weighted mean
    hru_centroid_locations = []
    for cat in allcats:
        hrus_with_cat = hru_cats[hru_cats == cat]
        if len(hrus_with_cat) == 1:
            hru_centroid_locations.append((hru_coords[hru_cats == cat]).squeeze())
        else:
            _centroids = hru_coords[hru_cats == cat]
            # print _centroids
            _areas = hru_areas[hru_cats == cat]
            # print _areas
            _x = np.average(_centroids[:, 0], weights=_areas)
            _y = np.average(_centroids[:, 1], weights=_areas)
            # print _x, _y
            hru_centroid_locations.append(np.array([_x, _y]))

    # Now upload weighted mean to database table
    # allcats and hru_centroid_locations are co-indexed
    index__cats = create_iterator(HRU)
    cur = hru.table.conn.cursor()
    for i in range(len(allcats)):
        # meters
        cur.execute(
            "update "
            + HRU
            + " set hru_x="
            + str(hru_centroid_locations[i][0])
            + " where cat="
            + str(allcats[i])
        )
        cur.execute(
            "update "
            + HRU
            + " set hru_y="
            + str(hru_centroid_locations[i][1])
            + " where cat="
            + str(allcats[i])
        )
        # feet
        cur.execute(
            "update "
            + HRU
            + " set hru_xlong="
            + str(hru_centroid_locations[i][0] * 3.28084)
            + " where cat="
            + str(allcats[i])
        )
        cur.execute(
            "update "
            + HRU
            + " set hru_ylat="
            + str(hru_centroid_locations[i][1] * 3.28084)
            + " where cat="
            + str(allcats[i])
        )
        # (un)Project to lat/lon
        _centroid_ll = gscript.parse_command(
            "m.proj", coordinates=list(hru_centroid_locations[i]), flags="od"
        ).keys()[0]
        _lon, _lat, _z = _centroid_ll.split("|")
        cur.execute(
            "update " + HRU + " set hru_lon=" + _lon + " where cat=" + str(allcats[i])
        )
        cur.execute(
            "update " + HRU + " set hru_lat=" + _lat + " where cat=" + str(allcats[i])
        )

    # feet -- not working.
    # Probably an issue with index__cats -- maybe fix later, if needed
    # But currently not a major speed issue
    """
    cur.executemany("update "+HRU+" set hru_xlong=?*3.28084 where hru_x=?",
                    index__cats)
    cur.executemany("update "+HRU+" set hru_ylat=?*3.28084 where hru_y=?",
                    index__cats)
    """

    cur.close()
    hru.table.conn.commit()
    hru.close()

    # ID NUMBER
    ############
    # cur.executemany("update "+HRU+" set hru_segment=? where id=?",
    #                index__cats)
    # Segment number = HRU ID number
    v.db_update(map=HRU, column="hru_segment", query_column="id", quiet=True)

    # LAND USE/COVER
    ############
    try:
        land_cover = int(land_cover)
    except:
        pass
    if isinstance(land_cover, int):
        if land_cover <= 3:
            v.db_update(map=HRU, column="cov_type", value=land_cover, quiet=True)
        else:
            sys.exit(
                "WARNING: INVALID LAND COVER TYPE. CHECK INTEGER VALUES.\n"
                "EXITING TO ALLOW USER TO CHANGE BEFORE RUNNING GSFLOW"
            )
    else:
        # NEED TO UPDATE THIS TO MODAL VALUE!!!!
        gscript.message(
            "Warning: values taken from HRU centroids. Code should be updated to"
        )
        gscript.message("acquire modal values")
        v.what_rast(
            map=HRU, type="centroid", raster=land_cover, column="cov_type", quiet=True
        )
        # v.rast_stats(map=HRU, raster=land_cover, method='average', column_prefix='tmp', flags='c', quiet=True)
        # v.db_update(map=HRU, column='cov_type', query_column='tmp_average', quiet=True)
        # v.db_dropcolumn(map=HRU, columns='tmp_average', quiet=True)

    # SOIL
    ############
    try:
        soil = int(soil)
    except:
        pass
    if isinstance(soil, int):
        if (soil > 0) and (soil <= 3):
            v.db_update(map=HRU, column="soil_type", value=soil, quiet=True)
        else:
            sys.exit(
                "WARNING: INVALID SOIL TYPE. CHECK INTEGER VALUES.\n"
                "EXITING TO ALLOW USER TO CHANGE BEFORE RUNNING GSFLOW"
            )
    else:
        # NEED TO UPDATE THIS TO MODAL VALUE!!!!
        gscript.message(
            "Warning: values taken from HRU centroids. Code should be updated to"
        )
        gscript.message("acquire modal values")
        v.what_rast(
            map=HRU, type="centroid", raster=soil, column="soil_type", quiet=True
        )
        # v.rast_stats(map=HRU, raster=soil, method='average', column_prefix='tmp', flags='c', quiet=True)
        # v.db_update(map=HRU, column='soil_type', query_column='tmp_average', quiet=True)
        # v.db_dropcolumn(map=HRU, columns='tmp_average', quiet=True)


if __name__ == "__main__":
    main()
