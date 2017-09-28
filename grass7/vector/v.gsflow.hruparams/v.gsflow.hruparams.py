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

#%module
#%  description: Set parameters for GSFLOW Hydrologic Response Units (HRUs)
#%  keyword: vector
#%  keyword: stream network
#%  keyword: hydrology
#%  keyword: GSFLOW
#%end

#%option G_OPT_R_INPUT
#%  key: elevation
#%  label: Elevation raster
#%  required: yes
#%  guidependency: layer,column
#%end

#%option G_OPT_V_INPUT
#%  key: input
#%  label: Sub-basins to become HRUs
#%  required: yes
#%  guidependency: layer,column
#%end

#%option G_OPT_V_OUTPUT
#%  key: output
#%  label: HRUs
#%  required: yes
#%  guidependency: layer,column
#%end

#%option
#%  key: slope
#%  type: string
#%  description: Slope [unitless]: r.slope.aspect format=percent zscale=0.01
#%  required: yes
#%end

#%option
#%  key: aspect
#%  type: string
#%  description: Aspect from r.slope.aspect
#%  required: yes
#%end

##################
# IMPORT MODULES #
##################
# PYTHON
import numpy as np
from matplotlib import pyplot as plt
import sys
# GRASS
from grass.pygrass.modules.shortcuts import general as g
from grass.pygrass.modules.shortcuts import raster as r
from grass.pygrass.modules.shortcuts import vector as v
from grass.pygrass.modules.shortcuts import miscellaneous as m
from grass.pygrass.gis import region
from grass.pygrass import vector # Change to "v"?
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
    Adds GSFLOW parameters to a set of HRU sub-basins
    """

    ##################
    # OPTION PARSING #
    ##################

    options, flags = gscript.parser()
    basins = options['input']
    HRU = options['output']
    slope = options['slope']
    aspect = options['aspect']
    elevation = options['elevation']

    ################################
    # CREATE HRUs FROM SUB-BASINS  #
    ################################

    g.copy(vector=(basins,HRU), overwrite=gscript.overwrite())

    ############################################
    # ATTRIBUTE COLUMNS (IN ORDER FROM MANUAL) #
    ############################################

    # HRU
    hru_columns = []
    # Self ID
    hru_columns.append('id integer') # nhru
    # Basic Physical Attributes (Geometry)
    hru_columns.append('hru_area double precision') # acres (!!!!)
    hru_columns.append('hru_area_m2 double precision') # [not for GSFLOW: for me!]
    hru_columns.append('hru_aspect double precision') # Mean aspect [degrees]
    hru_columns.append('hru_elev double precision') # Mean elevation
    hru_columns.append('hru_lat double precision') # Latitude of centroid
    hru_columns.append('hru_slope double precision') # Mean slope [percent]
    # Basic Physical Attributes (Other)
    #hru_columns.append('hru_type integer') # 0=inactive; 1=land; 2=lake; 3=swale; almost all will be 1
    #hru_columns.append('elev_units integer') # 0=feet; 1=meters. 0=default. I think I will set this to 1 by default.
    # Measured input
    hru_columns.append('outlet_sta integer') # Index of streamflow station at basin outlet:
                                             # station number if it has one, 0 if not
    # Note that the below specify projections and note lat/lon; they really seem
    # to work for any projected coordinates, with _x, _y, in meters, and _xlong, 
    # _ylat, in feet (i.e. they are just northing and easting). The meters and feet
    # are not just simple conversions, but actually are required for different
    # modules in the code, and are hence redundant but intentional.
    hru_columns.append('hru_x double precision') # Easting [m]
    hru_columns.append('hru_xlong double precision') # Easting [feet]
    hru_columns.append('hru_y double precision') # Northing [m]
    hru_columns.append('hru_ylat double precision') # Northing [feet]
    # Streamflow and lake routing
    hru_columns.append('K_coef double precision') # Travel time of flood wave to next downstream segment;
                                                  # this is the Muskingum storage coefficient
                                                  # 1.0 for reservoirs, diversions, and segments flowing
                                                  # out of the basin
    hru_columns.append('x_coef double precision') # Amount of attenuation of flow wave;
                                                  # this is the Muskingum routing weighting factor
                                                  # range: 0.0--0.5; default 0.2
                                                  # 0 for all segments flowing out of the basin
    hru_columns.append('hru_segment integer') # ID of stream segment to which flow will be routed
                                              # this is for non-cascade routing (flow goes directly
                                              # from HRU to stream segment)
    hru_columns.append('obsin_segment integer') # Index of measured streamflow station that replaces
                                                # inflow to a segment

    # Create strings
    hru_columns = ",".join(hru_columns)

    # Add columns to tables
    v.db_addcolumn(map=HRU, columns=hru_columns, quiet=True)


    ###########################
    # UPDATE DATABASE ENTRIES #
    ###########################

    colNames = np.array(gscript.vector_db_select(HRU, layer=1)['columns'])
    colValues = np.array(gscript.vector_db_select(HRU, layer=1)['values'].values())
    number_of_hrus = colValues.shape[0]
    cats = colValues[:,colNames == 'cat'].astype(int).squeeze()
    rnums = colValues[:,colNames == 'rnum'].astype(int).squeeze()

    nhru = np.arange(1, number_of_hrus + 1)
    nhrut = []
    for i in range(len(nhru)):
      nhrut.append( (nhru[i], cats[i]) )
    # Access the HRUs 
    hru = VectorTopo(HRU)
    # Open the map with topology:
    hru.open('rw')
    # Create a cursor
    cur = hru.table.conn.cursor()
    # Use it to loop across the table
    cur.executemany("update "+HRU+" set id=? where cat=?", nhrut)
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

    #hru_columns.append('hru_area double precision')
    # Acres b/c USGS
    v.to_db(map=HRU, option='area', columns='hru_area', units='acres', quiet=True)
    v.to_db(map=HRU, option='area', columns='hru_area_m2', units='meters', quiet=True)

    # GET MEAN VALUES FOR THESE NEXT ONES, ACROSS THE BASIN

    # SLOPE (and aspect) 
    #####################
    v.rast_stats(map=HRU, raster=slope, method='average', column_prefix='tmp', flags='c', quiet=True)
    v.db_update(map=HRU, column='hru_slope', query_column='tmp_average', quiet=True)

    # ASPECT
    #########
    v.db_dropcolumn(map=HRU, columns='tmp_average', quiet=True)
    # Dealing with conversion from degrees (no good average) to something I can
    # average -- x- and y-vectors
    # Geographic coordinates, so sin=x, cos=y.... not that it matters so long 
    # as I am consistent in how I return to degrees
    r.mapcalc('aspect_x = sin(' + aspect + ')', overwrite=gscript.overwrite(), quiet=True)
    r.mapcalc('aspect_y = cos(' + aspect + ')', overwrite=gscript.overwrite(), quiet=True)
    #grass.run_command('v.db.addcolumn', map=HRU, columns='aspect_x_sum double precision, aspect_y_sum double precision, ncells_in_hru integer')
    v.rast_stats(map=HRU, raster='aspect_x', method='sum', column_prefix='aspect_x', flags='c', quiet=True)
    v.rast_stats(map=HRU, raster='aspect_y', method='sum', column_prefix='aspect_y', flags='c', quiet=True)
    hru = VectorTopo(HRU)
    hru.open('rw')
    cur = hru.table.conn.cursor()
    cur.execute("SELECT cat,aspect_x_sum,aspect_y_sum FROM %s" %hru.name)
    _arr = np.array(cur.fetchall()).astype(float)
    _cat = _arr[:,0]
    _aspect_x_sum = _arr[:,1]
    _aspect_y_sum = _arr[:,2]
    aspect_angle = np.arctan2(_aspect_y_sum, _aspect_x_sum) * 180. / np.pi
    aspect_angle[aspect_angle < 0] += 360 # all positive
    aspect_angle_cat = np.vstack((aspect_angle, _cat)).transpose()
    cur.executemany("update "+ HRU +" set hru_aspect=? where cat=?", aspect_angle_cat)
    hru.table.conn.commit()
    hru.close()

    # ELEVATION
    ############
    v.rast_stats(map=HRU, raster=elevation, method='average', column_prefix='tmp', flags='c', quiet=True)
    v.db_update(map=HRU, column='hru_elev', query_column='tmp_average', quiet=True)
    v.db_dropcolumn(map=HRU, columns='tmp_average', quiet=True)

    # CENTROIDS -- NEED FIXING FOR TRUE CENTERS!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    ############

    # get x,y of centroid -- but have areas not in database table, that do have
    # centroids, and having a hard time finding a good way to get rid of them!
    # They have duplicate category values!
    # Perhaps these are little dangles on the edges of the vectorization where
    # the raster value was the same but pinched out into 1-a few cells?
    # From looking at map, lots of extra centroids on area boundaries, and removing
    # small areas (though threshold hard to guess) gets rid of these

    v.db_addcolumn(map=HRU, columns='centroid_x double precision, centroid_y double precision', quiet=True)
    v.to_db(map=HRU, type='centroid', columns='centroid_x, centroid_y', option='coor', units='meters', quiet=True)

    # hru_columns.append('hru_lat double precision') # Latitude of centroid
    colNames = np.array(gscript.vector_db_select(HRU, layer=1)['columns'])
    colValues = np.array(gscript.vector_db_select(HRU, layer=1)['values'].values())
    xy = colValues[:,(colNames=='centroid_x') + (colNames=='centroid_y')]
    np.savetxt('_xy.txt', xy, delimiter='|', fmt='%s')
    m.proj(flags='od', input='_xy.txt', output='_lonlat.txt', overwrite=True, quiet=True)
    lonlat = np.genfromtxt('_lonlat.txt', delimiter='|',)[:,:2]
    lonlat_cat = np.concatenate((lonlat, np.expand_dims(_cat, 2)), axis=1)

    # why not just get lon too?
    v.db_addcolumn(map=HRU, columns='hru_lon double precision')

    hru = VectorTopo(HRU)
    hru.open('rw')
    cur = hru.table.conn.cursor()
    cur.executemany("update "+ HRU +" set hru_lon=?, hru_lat=? where cat=?", lonlat_cat)
    hru.table.conn.commit()
    hru.close()

    # FIX!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # CENTROIDS ARE NOT REALLY CENTERS, AND DO NOT WORK IF THERE ARE MULTIPLE
    # AREAS
    # Pygrass to find area edges / cells, and get the center?
    # https://grass.osgeo.org/grass70/manuals/libpython/pygrass.vector.html

    # Easting and Northing for other columns
    v.db_update(map=HRU, column='hru_x', query_column='centroid_x', quiet=True)
    v.db_update(map=HRU, column='hru_xlong', query_column='centroid_x*3.28084', quiet=True) # feet
    v.db_update(map=HRU, column='hru_y', query_column='centroid_y', quiet=True)
    v.db_update(map=HRU, column='hru_ylat', query_column='centroid_y*3.28084', quiet=True) # feet

    # ID NUMBER
    ############

    """
    hru = VectorTopo(HRU)
    hru.open('rw')
    cur = hru.table.conn.cursor()
    cur.executemany("update "+HRU+" set hru_segment=? where id=?", hru_segmentt)
    hru.table.conn.commit()
    hru.close()
    """
    # Segment number = HRU ID number
    v.db_update(map=HRU, column='hru_segment', query_column='id', quiet=True)


if __name__ == "__main__":
    main()
