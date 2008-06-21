#!/bin/sh -x
#this script creates the database tables needed to store raster and temporal map informations

#create the raster and temporal tables
cat $GRAST4D_SQL_DIR/create_raster_table.sql | sed s/TABLE_NAME/$GRASTER_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_raster_time_table.sql | sed s/TABLE_NAME/$GRASTER_TIME_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_raster_metadata_table.sql | sed s/TABLE_NAME/$GRASTER_METADATA_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_temporal_raster_table.sql | sed s/TABLE_NAME/$GTEMPORAL_RASTER_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 
cat $GRAST4D_SQL_DIR/create_temporal_raster_metadata_table.sql | sed s/TABLE_NAME/$GTEMPORAL_RASTER_METADATA_TABLE_NAME/ | $GRAST4D_DBM $GRAST4D_DATABASE 

# create the raster view
echo  "create view $GRASTER_VIEW_NAME as select * from $GRASTER_TABLE_NAME, $GRASTER_TIME_TABLE_NAME, $GRASTER_METADATA_TABLE_NAME where $GRASTER_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name AND $GRASTER_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name AND $GRASTER_METADATA_TABLE_NAME.name = $GRASTER_TIME_TABLE_NAME.name;" | $GRAST4D_DBM $GRAST4D_DATABASE

#register trigger functions

echo "SQL tables created"
