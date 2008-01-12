#!/bin/sh
# functions to insert or update raster map entries to the grass sql database 

source globals/defines.sh

#this var is used to store the computed sqlite timestamps
GLOBAL_DATE_VAR="" 

#pasre the grass date format and convert it into sqlite date format
parse_timestamp() #arguments are DAY MONTH YEAR TIME
{
DAY=$1
MONTH=$2
YEAR=$3
TIME=$4

# change the month to MM!!!! :/
MONTH=`echo $MONTH | sed s/Jan/01/`
MONTH=`echo $MONTH | sed s/Feb/02/`
MONTH=`echo $MONTH | sed s/Mar/03/`
MONTH=`echo $MONTH | sed s/Apr/04/`
MONTH=`echo $MONTH | sed s/May/05/`
MONTH=`echo $MONTH | sed s/Jun/06/`
MONTH=`echo $MONTH | sed s/Jul/07/`
MONTH=`echo $MONTH | sed s/Aug/08/`
MONTH=`echo $MONTH | sed s/Sep/09/`
MONTH=`echo $MONTH | sed s/Oct/10/`
MONTH=`echo $MONTH | sed s/Nov/11/`
MONTH=`echo $MONTH | sed s/Dec/12/`
#change the day to DD
if [ `expr $DAY \< 10` -eq 1 ] ; then
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
GROUP_TABLE="${RASTER_GROUP_TABLE_PREFIX}_${MAPNAME}"
REFERENCE_TABLE="${RASTER_REFERENCE_TABLE_PREFIX}_${MAPNAME}"
METADATA_TABLE="${RASTER_METADATA_TABLE_PREFIX}_${MAPNAME}"
CATEGORY_TABLE="${RASTER_CATEGORY_TABLE_PREFIX}_${MAPNAME}"
TEMPORAL_TABLE="${RASTER_TEMPORAL_TABLE_PREFIX}_${MAPNAME}"

# get the number of cats
CAT_NUM=`r.info $MAPNAME | grep "Categories:" | awk '{print $9}'` 

# create or update the database table
STRING=`$DBM $DATABASE "select name from $RASTER_TABLE_NAME where name='$MAPNAME'"`
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $RASTER_TABLE_NAME ENTRY $MAPNAME"

  SQL_DATATYPE_STRING="(name, base_map, reference_table, color, group_table, temporal_table, metadata_table, category_table, category_num)"
  SQL_VALUE_STRING="('$MAPNAME', '$BASE_MAP', '$REFERENCE_TABLE','$COLOR', '$GROUP_TABLE', '$TEMPORAL_TABLE', '$METADATA_TABLE', '$CATEGORY_TABLE', '$CAT_NUM')"

  $DBM $DATABASE "INSERT INTO $RASTER_TABLE_NAME $SQL_DATATYPE_STRING values $SQL_VALUE_STRING"

  #create the raster map tables
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$REFERENCE_TABLE/ | $DBM $DATABASE 
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$GROUP_TABLE/ | $DBM $DATABASE 
  #cat $SQL_DIR/create_name_list_table.sql | sed s/TABLE_NAME/$TEMPORAL_TABLE/ | $DBM $DATABASE 
  #cat $SQL_DIR/create_raster_metadata_table.sql | sed s/TABLE_NAME/$METADATA_TABLE/ | $DBM $DATABASE 
  #cat $SQL_DIR/create_raster_categorie_table.sql | sed s/TABLE_NAME/$CATEGORY_TABLE/ | $DBM $DATABASE 

else
  echo "UPDATE $RASTER_TABLE_NAME ENTRY $MAPNAME"
  $DBM $DATABASE "UPDATE $RASTER_TABLE_NAME SET base_map='$BASE_MAP' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $RASTER_TABLE_NAME SET color='$COLOR' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $RASTER_TABLE_NAME SET category_num='$CAT_NUM' WHERE name='$MAPNAME'"
fi
}

#insert or update an entry in the global raster metadata table
insert_raster_map_metadata ()
{
MAPNAME=$1
METADATA_TABLE="${RASTER_METADATA_TABLE_NAME}"
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
STRING=`$DBM $DATABASE "select name from $METADATA_TABLE where name='$MAPNAME'"` 
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $METADATA_TABLE ENTRY $MAPNAME"
  SQL_DATATYPE_STRING="(name, projection, datatype, rows, cols, cell_num, north, south, west, east, ns_res,
		      ew_res, min, max, mtime, creator, data_source, comments, description, additional_data)"
  SQL_VALUE_STRING="('$MAPNAME', '$PROJECTION', '$datatype', '$ROWS', '$COLS', '$CELLNUM', '$north', '$south', '$west', '$east', 
		   '$nsres' , '$ewres', '$min', '$max', $MTIME, '$CREATOR', '$DATA_SOURCE', '$COMMENTS', '$DESCRIPTION' , '$ADDITIONAL_DATA')"  
  $DBM $DATABASE "INSERT INTO $METADATA_TABLE $SQL_DATATYPE_STRING values $SQL_VALUE_STRING"
else
  echo "UPDATE $METADATA_TABLE ENTRY $MAPNAME"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET projection='$PROJECTION' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET datatype='$datatype' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET rows='$ROWS' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET cols='$COLS' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET cell_num='$CELLNUM' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET north='$north' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET south='$south' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET west='$west' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET east='$east' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET ns_res='$nsres' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET ew_res='$ewres' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET min='$min' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET max='$max' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET mtime=$MTIME WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET creator='$CREATOR' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET data_source='$DATA_SOURCE' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET comments='$COMMENTS' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET description='$DESCRIPTION' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $METADATA_TABLE SET additional_data='$ADDITIONAL_DATA' WHERE name='$MAPNAME'"
fi

}

# insert or update a raster map entry in the raster map time table
insert_raster_map_time () 
{
MAPNAME=$1
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
VTIME_END="DATETIME('$VTIME_START', '+10 years')"

#echo $CTIME
#echo $MTIME
#echo $VTIME_START
#echo $VTIME_END

# insert or update 
STRING=`$DBM $DATABASE "select name from $RASTER_TIME_TABLE_NAME where name='$MAPNAME'"`
if [ "$STRING" = "" ] ; then
  echo "INSERT NEW $RASTER_TIME_TABLE_NAME ENTRY $MAPNAME"

  SQL_DATATYPE_STRING="(name, ctime, mtime, vtime_start, vtime_end)"
  SQL_VALUE_STRING="('$MAPNAME', '$CTIME', $MTIME, '$VTIME_START', $VTIME_END)"

  $DBM $DATABASE "INSERT INTO $RASTER_TIME_TABLE_NAME $SQL_DATATYPE_STRING values $SQL_VALUE_STRING"

else
  echo "UPDATE $RASTER_TIME_TABLE_NAME ENTRY $MAPNAME"
  $DBM $DATABASE "UPDATE $RASTER_TIME_TABLE_NAME SET ctime='$CTIME' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $RASTER_TIME_TABLE_NAME SET mtime=$MTIME WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $RASTER_TIME_TABLE_NAME SET vtime_start='$VTIME_START' WHERE name='$MAPNAME'"
  $DBM $DATABASE "UPDATE $RASTER_TIME_TABLE_NAME SET vtime_end=$VTIME_END WHERE name='$MAPNAME'"
fi
exit
}

