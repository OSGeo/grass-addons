#!/bin/sh
#this script creates the database tables needed to store raster and temporal map informations

#create the raster and temporal tables
cat $SQL_DIR/create_raster_table.sql | sed s/TABLE_NAME/$RASTER_TABLE_NAME/ | $DBM $DATABASE 
cat $SQL_DIR/create_raster_time_table.sql | sed s/TABLE_NAME/$RASTER_TIME_TABLE_NAME/ | $DBM $DATABASE 
cat $SQL_DIR/create_raster_metadata_table.sql | sed s/TABLE_NAME/$RASTER_METADATA_TABLE_NAME/ | $DBM $DATABASE 
cat $SQL_DIR/create_temporal_raster_table.sql | sed s/TABLE_NAME/$TEMPORAL_RASTER_TABLE_NAME/ | $DBM $DATABASE 
cat $SQL_DIR/create_temporal_raster_metadata_table.sql | sed s/TABLE_NAME/$TEMPORAL_RASTER_METADATA_TABLE_NAME/ | $DBM $DATABASE 

# create the raster view
echo  "create view $RASTER_VIEW_NAME as select * from $RASTER_TABLE_NAME, $RASTER_TIME_TABLE_NAME, $RASTER_METADATA_TABLE_NAME where $RASTER_TABLE_NAME.name = $RASTER_TIME_TABLE_NAME.name AND $RASTER_TABLE_NAME.name = $RASTER_TIME_TABLE_NAME.name AND $RASTER_METADATA_TABLE_NAME.name = $RASTER_TIME_TABLE_NAME.name;" | $DBM $DATABASE

#register trigger functions

echo "SQL tables created"
