#!/bin/sh

### setup enviro vars ###
eval `g.gisenv`
: ${GISBASE?} ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}

#definitions
#export GRAST4D_BASE="`pwd`"
export GRAST4D_BASE=${GISDBASE}/${LOCATION_NAME}/${MAPSET}
export GRAST4D_DB_DIR="$GRAST4D_BASE/rast4d_db"

##############################
export GRAST4D_BIN_DIR="${GISBASE}/etc/r.rast4d/bin"
export GRAST4D_LIB_DIR="${GISBASE}/etc/r.rast4d/lib"
export GRAST4D_SQL_DIR="${GISBASE}/etc/r.rast4d/sql"
export PATH=$GRAST4D_BIN_DIR:$PATH
# SQLite:
export GRAST4D_DATABASE=$GRAST4D_DB_DIR/database.sqlite
export GRAST4D_DBM="sqlite3"
# PostgreSQL:
#export PGDB=rast4d_database
#export GRAST4D_DATABASE="-h localhost -p 5432 -U $USER $PGDB"
#export GRAST4D_DBM="psql"

# Table name definitions
export GRASTER_VIEW_NAME="raster_view"
export GRASTER_TABLE_NAME="raster_table"
export GRASTER_TIME_TABLE_NAME="raster_time_table"
export GRASTER_METADATA_TABLE_NAME="raster_metadata_table"
export GTEMPORAL_VIEW_NAME="temporal_view"
export GTEMPORAL_RASTER_TABLE_NAME="temporal_raster_table"
export GTEMPORAL_RASTER_METADATA_TABLE_NAME="temporal_raster_metadata_table"

export GRASTER_REFERENCE_TABLE_PREFIX="raster_reference_table"
export GRASTER_GROUP_TABLE_PREFIX="raster_group_table"
export GRASTER_TEMPORAL_TABLE_PREFIX="raster_temporal_table"
export GRASTER_METADATA_TABLE_PREFIX="raster_metadata_table"
export GRASTER_CATEGORY_TABLE_PREFIX="raster_category_table"

