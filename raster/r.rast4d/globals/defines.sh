#!/bin/sh

#definitions
export BASE="`pwd`"
export DB_DIR="$BASE/db"
export BIN_DIR="$BASE/bin"
export LIB_DIR="$BASE/lib"
export SQL_DIR="$BASE/sql"
export DATABASE=$DB_DIR/database.sqlite
export PATH=$BIN_DIR:$PATH
export DBM="sqlite3"

# Table name definitions
export RASTER_VIEW_NAME="raster_view"
export RASTER_TABLE_NAME="raster_table"
export RASTER_TIME_TABLE_NAME="raster_time_table"
export RASTER_METADATA_TABLE_NAME="raster_metadata_table"
export TEMPORAL_VIEW_NAME="temporal_view"
export TEMPORAL_RASTER_TABLE_NAME="temporal_raster_table"
export TEMPORAL_RASTER_METADATA_TABLE_NAME="temporal_raster_metadata_table"

export RASTER_REFERENCE_TABLE_PREFIX="raster_reference_table"
export RASTER_GROUP_TABLE_PREFIX="raster_group_table"
export RASTER_TEMPORAL_TABLE_PREFIX="raster_temporal_table"
export RASTER_METADATA_TABLE_PREFIX="raster_metadata_table"
export RASTER_CATEGORY_TABLE_PREFIX="raster_category_table"

