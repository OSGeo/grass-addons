#!/bin/sh
# functions to insert or update raster map entries to the grass sql database 

### setup enviro vars ###
eval `g.gisenv`
: ${GISBASE?} ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}

source ${GISBASE}/etc/r.rast4d/globals/defines.sh

#this var is used to store the computed sqlite timestamps
GLOBAL_DATE_VAR="" 

#pasre the grass date format and convert it into sqlite date format
parse_timestamp() #arguments are DAY MONTH YEAR TIME
{
    local DAY=$1 MONTH=$2 YEAR=$3 TIME=$4

    # change the month to MM!!!! :/
    MONTH=$(echo "$MONTH" \
                | sed -e s/Jan/01/ -e s/Feb/02/ -e s/Mar/03/ \
                      -e s/Apr/04/ -e s/May/05/ -e s/Jun/06/ \
                      -e s/Jul/07/ -e s/Aug/08/ -e s/Sep/09/ \
                      -e s/Oct/10/ -e s/Nov/11/ -e s/Dec/12/)

    # change the day to DD
    if [ $DAY -lt 10 ] ; then
        DAY="0$DAY"
    fi

GLOBAL_DATE_VAR="$YEAR-$MONTH-$DAY $TIME"
}


# insert or update a raster map entry in the raster map table
insert_raster_map () 
{
MAPNAME=$1
BASE_MAP=""
COLOR="unknown"
CAT_NUM=""
GROUP_TABLE="${GRASTER_GROUP_TABLE_PREFIX}_${MAPNAME}"
REFERENCE_TABLE="${GRASTER_REFERENCE_TABLE_PREFIX}_${MAPNAME}"
METADATA_TABLE="${GRASTER_METADATA_TABLE_PREFIX}_${MAPNAME}"
CATEGORY_TABLE="${GRASTER_CATEGORY_TABLE_PREFIX}_${MAPNAME}"
TEMPORAL_TABLE="${GRASTER_TEMPORAL_TABLE_PREFIX}_${MAPNAME}"

# get the number of cats
CAT_NUM=`r.info $MAPNAME | grep "Categories:" | awk '{print $9}'` 

# create or update the database table
STRING=`echo "SELECT name FROM $GRASTER_TABLE_NAME WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE`
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $GRASTER_TABLE_NAME ENTRY $MAPNAME"

  SQL_DATATYPE_STRING="(name, base_map, reference_table, color, group_table, temporal_table, metadata_table, category_table, category_num)"
  SQL_VALUE_STRING="('$MAPNAME', '$BASE_MAP', '$REFERENCE_TABLE','$COLOR', '$GROUP_TABLE', '$TEMPORAL_TABLE', '$METADATA_TABLE', '$CATEGORY_TABLE', '$CAT_NUM')"

  echo "INSERT INTO $GRASTER_TABLE_NAME $SQL_DATATYPE_STRING values $SQL_VALUE_STRING;" | $GRAST4D_DBM $GRAST4D_DATABASE

  #create the raster map tables
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$REFERENCE_TABLE/ | $GRAST4D_DBM $GRAST4D_DATABASE 
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$GROUP_TABLE/ | $GRAST4D_DBM $GRAST4D_DATABASE 
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$TEMPORAL_TABLE/ | $GRAST4D_DBM $GRAST4D_DATABASE 
  #cat $SQL_DIR/create_raster_metadata_table.sql | sed s/TABLE_NAME/$METADATA_TABLE/ | $GRAST4D_DBM $GRAST4D_DATABASE 
  #cat $SQL_DIR/create_raster_categorie_table.sql | sed s/TABLE_NAME/$CATEGORY_TABLE/ | $GRAST4D_DBM $GRAST4D_DATABASE 

else
  echo "UPDATE $GRASTER_TABLE_NAME ENTRY $MAPNAME"
  echo "UPDATE $GRASTER_TABLE_NAME SET base_map='$BASE_MAP' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $GRASTER_TABLE_NAME SET color='$COLOR' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $GRASTER_TABLE_NAME SET category_num='$CAT_NUM' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
fi
}

#insert or update an entry in the global raster metadata table
insert_raster_map_metadata ()
{
MAPNAME=$1
METADATA_TABLE="${GRASTER_METADATA_TABLE_NAME}"
PROJECTION=`g.proj -w`
ROWS=`r.info $MAPNAME | grep "Rows:" | awk '{print $3}'`
COLS=`r.info $MAPNAME | grep "Columns" | awk '{print $3}'`
CELLNUM=`r.info $MAPNAME | grep "Total Cells:" | awk '{print $4}'`
eval `r.info -t $MAPNAME`
eval `r.info -g $MAPNAME`
eval `r.info -s $MAPNAME`
eval `r.info -r $MAPNAME`
CREATOR=`r.info $MAPNAME | grep "Login of Creator:" | awk '{print $7}'`
MTIME="DATETIME('NOW')"
COMMENTS=`r.info -h $MAPNAME`
DATA_SOURCE=""
DESCRIPTION=""
ADDITIONAL_DATA=""

#echo $MAPNAME
#echo $METADATA_TABLE
#echo $PROJECTION
#echo $ROWS
#echo $COLS
#echo $CELLNUM
#echo $datatype
#echo $north
#echo $south
#echo $west
#echo $east
#echo $nsres
#echo $ewres
#echo $min
#echo $max
#echo $CREATOR
#echo $MTIME
#echo $DATA_SOURCE
#echo $COMMENTS
#echo $DESCRIPTION
#echo $ADDITIONAL_DATA


# insert or update
STRING=`echo "select name from $METADATA_TABLE where name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE` 
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $METADATA_TABLE ENTRY $MAPNAME"
  SQL_DATATYPE_STRING="(name, projection, datatype, rows, cols, cell_num, north, south, west, east, ns_res,
		      ew_res, min, max, mtime, creator, data_source, comments, description, additional_data)"
  SQL_VALUE_STRING="('$MAPNAME', '$PROJECTION', '$datatype', '$ROWS', '$COLS', '$CELLNUM', '$north', '$south', '$west', '$east', 
		   '$nsres' , '$ewres', '$min', '$max', $MTIME, '$CREATOR', '$DATA_SOURCE', '$COMMENTS', '$DESCRIPTION' , '$ADDITIONAL_DATA')"  
  echo "INSERT INTO $METADATA_TABLE $SQL_DATATYPE_STRING values $SQL_VALUE_STRING;" | $GRAST4D_DBM $GRAST4D_DATABASE 
else
  echo "UPDATE $METADATA_TABLE ENTRY $MAPNAME"
  echo "UPDATE $METADATA_TABLE SET projection='$PROJECTION' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET datatype='$datatype' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET rows='$ROWS' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET cols='$COLS' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET cell_num='$CELLNUM' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET north='$north' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET south='$south' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET west='$west' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET east='$east' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET ns_res='$nsres' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET ew_res='$ewres' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET min='$min' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET max='$max' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET mtime=$MTIME WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET creator='$CREATOR' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET data_source='$DATA_SOURCE' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET comments='$COMMENTS' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET description='$DESCRIPTION' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $METADATA_TABLE SET additional_data='$ADDITIONAL_DATA' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
fi

}

# insert or update a raster map entry in the raster map time table
insert_raster_map_time () 
{
MAPNAME=$1
MY_VTIME_END="$2"
YEAR=`r.info $MAPNAME | grep Date: | awk '{print $9}'`
MONTH=`r.info $MAPNAME | grep Date: | awk '{print $6}'`
DAY=`r.info $MAPNAME | grep Date: | awk '{print $7}'`
TIME=`r.info $MAPNAME | grep Date: | awk '{print $8}'`

# the sqlite3 time format is YYYY-MM-DD HH:MM:SS
parse_timestamp $DAY $MONTH $YEAR $TIME 
CTIME=$GLOBAL_DATE_VAR
MTIME="DATETIME('NOW')"

#the real grass timestamps
DAY=`r.timestamp $MAPNAME | awk '{print $1}'`
MONTH=`r.timestamp $MAPNAME | awk '{print $2}'` 
YEAR=`r.timestamp $MAPNAME | awk '{print $3}'` 
TIME=`r.timestamp $MAPNAME | awk '{print $4}'` 
# the sqlite3 time format is YYYY-MM-DD HH:MM:SS
parse_timestamp $DAY $MONTH $YEAR $TIME 
VTIME_START=$GLOBAL_DATE_VAR
VTIME_END="DATETIME('$VTIME_START', '$MY_VTIME_END')"

#echo $CTIME
#echo $MTIME
#echo $VTIME_START
#echo $VTIME_END

# insert or update 
STRING=`echo "select name from $GRASTER_TIME_TABLE_NAME where name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE`
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $GRASTER_TIME_TABLE_NAME ENTRY $MAPNAME"

  SQL_DATATYPE_STRING="(name, ctime, mtime, vtime_start, vtime_end)"
  SQL_VALUE_STRING="('$MAPNAME', '$CTIME', $MTIME, '$VTIME_START', $VTIME_END)"

  echo "INSERT INTO $GRASTER_TIME_TABLE_NAME $SQL_DATATYPE_STRING values $SQL_VALUE_STRING;" | $GRAST4D_DBM $GRAST4D_DATABASE

else
  echo "UPDATE $GRASTER_TIME_TABLE_NAME ENTRY $MAPNAME"
  echo "UPDATE $GRASTER_TIME_TABLE_NAME SET ctime='$CTIME' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $GRASTER_TIME_TABLE_NAME SET mtime=$MTIME WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $GRASTER_TIME_TABLE_NAME SET vtime_start='$VTIME_START' WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
  echo "UPDATE $GRASTER_TIME_TABLE_NAME SET vtime_end=$VTIME_END WHERE name='$MAPNAME';" | $GRAST4D_DBM $GRAST4D_DATABASE
 # difference in days
  echo "UPDATE $GRASTER_TIME_TABLE_NAME SET vtime_duration=(strftime('%s',vtime_end) - (SELECT strftime('%s',vtime_start)))/86400.0;" | $GRAST4D_DBM $GRAST4D_DATABASE
fi
exit
}

