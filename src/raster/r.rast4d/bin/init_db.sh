#!/bin/sh

#this script creates the database tables needed to store raster and temporal map informations

#create the raster and temporal tables
cat $GRAST4D_SQL_DIR/create_raster_table.sql | sed s/TABLE_NAME/$GRASTER_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_raster_time_table.sql | sed s/TABLE_NAME/$GRASTER_TIME_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_raster_metadata_table.sql | sed s/TABLE_NAME/$GRASTER_METADATA_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_temporal_raster_table.sql | sed s/TABLE_NAME/$GTEMPORAL_RASTER_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_temporal_raster_metadata_table.sql | sed s/TABLE_NAME/$GTEMPORAL_RASTER_METADATA_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 

# create the raster view
## bug: replicates columns:
#echo  "create view $GRASTER_VIEW_NAME as select * from $GRASTER_TABLE_NAME, $GRASTER_TIME_TABLE_NAME, $GRASTER_METADATA_TABLE_NAME \
#       where $GRASTER_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name AND $GRASTER_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name \
#       AND $GRASTER_METADATA_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name;" | $GRAST4D_DBM $GRAST4D_DATABASE

echo  "CREATE VIEW raster_view AS SELECT rt.*, rtt.ctime,rtt.mtime,rtt.vtime_start,rtt.vtime_end,rtt.vtime_duration, \
       rmt.projection, rmt.datatype, rmt.rows, rmt.cols, rmt.cell_num, rmt.north, rmt.south, rmt.west, rmt.east, rmt.ns_res, \
       rmt.ew_res, rmt.min, rmt.max, rmt.creator, rmt.data_source, rmt.comments, rmt.description, rmt.additional_data \
       from raster_table as rt, raster_time_table as rtt, raster_metadata_table as rmt \
       WHERE rt.name = rtt.name AND rt.name = rtt.name AND rmt.name = rtt.name;" | $GRAST4D_DBM $GRAST4D_DATABASE

#register trigger functions

echo "SQL tables created"
