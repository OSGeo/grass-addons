#!/bin/sh
#
############################################################################
#
# MODULE:       v.in.postgis.sh
# AUTHOR(S):	Mathieu Grelier, 2007 (greliermathieu@gmail.com)
# PURPOSE:		postgis data manipulation in grass from arbitrary sql queries
# COPYRIGHT:	(C) 2007 Mathieu Grelier
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################


#%Module
#%  description: Create a grass layer from any sql query in postgis 
#%  keywords: postgis, grass layer, sql 
#%End
#%option
#% key: query
#% type: string
#% description: Any sql query returning a recordset with geometry for each row 
#% required : yes
#%end
#%option
#% key: geometryfield
#% type: string
#% answer: the_geom
#% description: Name of the source geometry field (usually defaults to the_geom)
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% answer: v_in_postgis
#% description: Name of the imported grass layer (do not use capital letters)
#% required : no
#%end
#%flag
#% key: d
#% description: Import result in grass dbf format (no new table in postgis - if not set, new grass layer attributes will be connected to the result table)
#%end
#%flag
#% key: r
#% description: Use -o for v.in.ogr (override dataset projection)
#%end
#%flag
#% key: g
#% description: Add a gist index to the imported result table in postgis (useless with the d flag)
#%end

if  [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program."
 	exit 1
fi   

if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi

## Config : you may need to fix these values
#####################################
#uncomment one of the home dir line depending on your system
#linux
homedir="$HOME"
#windows (fix this path as it depends on the user login)
#homedir="C:\Documents and Settings\your.login"

#fix this path
if [ -z "$LOGDIR" ] ; then
	LOGDIR="$HOME"
fi

#default for grass6
grassloginfile="$homedir"/.grasslogin6

## GRASS team recommandations
#####################################

PROG=`basename $0`

# check if we have awk
if [ ! -x "`which awk`" ] ; then
    echo "$PROG: awk required, please install awk or gawk first"
    exit 1
fi

# setting environment, so that awk works properly in all languages
unset LC_ALL
LC_NUMERIC=C
export LC_NUMERIC

## exit procedures
#####################################

scriptend()
{   
	\rm -f "$TMPFILE1"
	\rm -f "$TMPFILE2"
}

userbreakprocedure()
{
    echo "User break!"
	scriptend
}
# shell check for user break (signal list: trap -l)
trap "userbreakprocedure" 2 3 6 9 15 19

#callable only after data has been imported
scripterror()
{
	echo "script end cleanup:" >> "$LOGFILE" 2>&1	
	echo "try to remove temp postgis table" >> "$LOGFILE" 2>&1
	echo "DROP TABLE "$GIS_OPT_OUTPUT"" | db.execute >> "$TMPFILE2" 2>&1
	echo "try to remove temp grass layer" >> "$LOGFILE" 2>&1
	g.remove vect=tmpoutput >> "$TMPFILE2" 2>&1	
	echo "execution failed" >> "$LOGFILE"
	echo "script end cleanup:" >> "$LOGFILE" 2>&1
	scriptend
	exit 1
}

scriptsuccess()
{
	echo "execution ok" >> "$LOGFILE"	
	echo "script end cleanup:" >> "$LOGFILE" 2>&1	
	scriptend
	exit 0
}

## necessary checks
#####################################

#this file will collect info from stdout and stderr (v.in.ogr for example outputs on stderr).
LOGFILE="$LOGDIR/v.in.postgis.QUERY.log"

TMPFILE1="`g.tempfile pid=$$`"
TMPFILE2="`g.tempfile pid=$$`"
if [ $? -ne 0 ] || [ -z "$TMPFILE1" ] || [ -z "$TMPFILE2" ]; then
	echo "ERROR: unable to create temporary files" 1>&2
fi

echo "v.in.postgis.QUERY:" >> "$LOGFILE"
echo "$GIS_OPT_QUERY" >> "$LOGFILE"

echo "check if .grasslogin file is found:" >> "$LOGFILE"
if [ ! -r "$grassloginfile" ] ;then
	echo "ERROR: .grasslogin file was not found. Use db.login before using this script or modify the config section in the script." 1>&2
	scriptend
	exit 1
fi

echo "check if grass layer already exists:" >> "$LOGFILE"
eval `g.findfile element=vector file="$GIS_OPT_OUTPUT"`	
if [ "$file" ] ; then
	if [ -z "$GRASS_OVERWRITE" ] || [ "$GRASS_OVERWRITE" -eq 0 ]; then
		echo "ERROR: vector map '$GIS_OPT_OUTPUT' already exists in mapset search path. Use the --o flag to overwrite or remove it before." 1>&2
		scriptend
		exit 1
	else
		echo "WARNING: vector map '$GIS_OPT_OUTPUT' will be overwritten." >> "$LOGFILE" 2>&1
		#we must use g.remove to implement overwrite as it is not a valid option of v.in.ogr for now
		g.remove vect="$GIS_OPT_OUTPUT" >> "$LOGFILE" 2>&1
	fi
fi

#previous script execution may have not removed temporary elements
echo "script start cleanup:" >> "$LOGFILE" 2>&1
#test if a GIS_OPT_OUTPUT table already exists. If yes, was it created by this script ? If yes, delete it.
echo "SELECT CAST(tablename AS text) FROM pg_tables WHERE schemaname='public'" | db.select -c > "$TMPFILE1"
if grep -q -x "$GIS_OPT_OUTPUT" "$TMPFILE1" ; then 
	comment=$(echo "SELECT obj_description((SELECT c.oid FROM pg_catalog.pg_class c WHERE c.relname='"$GIS_OPT_OUTPUT"'), 'pg_class') AS comment" | db.select -c)
	if [ "$comment" = "created_with_v.in.postgis.sh" ]; then
		echo "DROP TABLE "$GIS_OPT_OUTPUT"" | db.execute >> "$TMPFILE2" 2>&1
	else
		echo "ERROR: a table with the name "$GIS_OPT_OUTPUT" already exists and was not created by this script." 1>&2
		scriptend
		exit 1
	fi
fi

## import
######################################
#must be done before call.
#db.login ...
#db.connect ...

#grass doesn't support importing postgis views
#So we use a create table as statement to import a kind of view with v.in.ogr
echo "try to import data:" >> "$LOGFILE" 2>&1
echo "CREATE TABLE "$GIS_OPT_OUTPUT" AS ""$GIS_OPT_QUERY" | db.execute >> "$LOGFILE" 2>&1
if [ $? -ne 0 ] ; then
	echo "ERROR: an error occurred during sql import. Check your connection to the database and your sql query." 1>&2
	scriptend
	exit 1
fi
#we use also postgres comments as a specific mark for these tables. When we delete this table in the cleanup procedure using the layer name, we will check for this mark to ensure another table is not deleted, if the given layer name correspond to an existing table in the database. 
echo "COMMENT ON TABLE "$GIS_OPT_OUTPUT" IS 'created_with_v.in.postgis.sh'" | db.execute >> "$LOGFILE" 2>&1
if [ $? -ne 0 ] ; then
	echo "ERROR: an error occurred during commenting the table." 1>&2
	scripterror
fi

#if -d flag wasn't not selected, can't import if query result already have a cat column
#todo : add cat_ column in this case, as v.in.ogr with dbf driver do 
if [ "$GIS_FLAG_D" -eq 0 ] ; then
	tmp_pkey_name="tmp_pkey"_"$GIS_OPT_OUTPUT"
	#with the pg driver (not the dbf one), v.in.ogr need a 'cat' column for index creation 
	echo "ALTER TABLE "$GIS_OPT_OUTPUT" ADD COLUMN cat serial NOT NULL" | db.execute >> "$LOGFILE" 2>&1
	if [ $? -ne 0 ] ; then
		echo "WARNING: unable to add a 'cat' column. A column named 'CAT' or 'cat' may be present in your input data. This column is reserved for Grass to store categories."  1>&2
	fi
	echo "ALTER TABLE "$GIS_OPT_OUTPUT" ADD CONSTRAINT "$tmp_pkey_name" PRIMARY KEY (cat)" | db.execute >> "$LOGFILE" 2>&1
	if [ $? -ne 0 ] ; then
		echo "ERROR: unable to add temporary primary key" 1>&2
		scripterror
	fi
fi

#we need to use the postgis AddGeometryColumn function so that v.in.ogr will work. 
echo "retrieving geometry info:" >> "$LOGFILE"
#first, which table?
geometry_column="$GIS_OPT_GEOMETRYFIELD"
#if there is more than one geometry type in the query result table, we use the generic GEOMETRY type
echo "SELECT DISTINCT GeometryType("$geometry_column") FROM "$GIS_OPT_OUTPUT"" | db.select -c > "$TMPFILE1"
nb=$(cat "$TMPFILE1" | wc -l)
if [ "$nb" -eq 1 ] ; then
	type=$(awk '{print $1}' "$TMPFILE1")
	echo "type=$type" >> "$LOGFILE" 2>&1
else
	type="GEOMETRY"
fi
#same thing with number of dimensions. If the query is syntactically correct but returns no geometry, this step will cause an error.
echo "SELECT DISTINCT ndims("$geometry_column") FROM "$GIS_OPT_OUTPUT"" | db.select -c > "$TMPFILE1"
nb=$(cat "$TMPFILE1" | wc -l)
echo "number of dimensions=$nb" >> "$LOGFILE" 2>&1
if [ "$nb" -eq 1 ] ; then
	coord_dimension=$(awk '{print $1}' "$TMPFILE1")
	echo "coord_dimension=$coord_dimension" >> "$LOGFILE" 2>&1
else
	echo "ERROR: the script was unable to retrieve a unique coordinates dimension for this query or no geometry is present. Check your sql query. " 1>&2
	scripterror
fi
#srid
echo "SELECT DISTINCT srid("$geometry_column") FROM "$GIS_OPT_OUTPUT"" | db.select -c > "$TMPFILE1"
nb=$(cat "$TMPFILE1" | wc -l)
if [ "$nb" -eq 1 ] ; then
	srid=$(awk '{print $1}' "$TMPFILE1")
	echo "srid=$srid" >> "$LOGFILE" 2>&1
else
	srid="-1"
	echo "WARNING: the script was unable to retrieve a unique geometry srid for this query. Using undefined srid." 1>&2
fi
if [ $? -ne 0 ] ; then
	echo "ERROR: the script was unable to retrieve geometry parameters" 1>&2
	scripterror
fi

#we must remove other geometry columns than selected one that may be present in the query result, because v.in.ogr does not allow geometry columns selection
#v.in.ogr take the first geometry column found in the table so if another geometry is present, as we use AddGeometryColumn fonction to copy selected geometry (see below), our geometry will appear after other geometries in the column list. In this case, v.in.ogr would not import the right geometry.
echo "Checking for other geometries" >> "$LOGFILE"
echo "SELECT column_name FROM(SELECT ordinal_position, column_name, udt_name FROM INFORMATION_SCHEMA.COLUMNS WHERE (TABLE_NAME='"$GIS_OPT_OUTPUT"') order by ordinal_position) as info WHERE udt_name='geometry' AND NOT column_name='"$geometry_column"'" | db.select -c > "$TMPFILE1" 2>> "$LOGFILE" 
while read other_geo_column
do
if [ -n "$other_geo_column" ]; then 
	echo "Found another geometry in the query result than selected one : ""$other_geo_column"" . Column will be dropped." >> "$LOGFILE"
	echo "ALTER TABLE "$GIS_OPT_OUTPUT" DROP COLUMN "$other_geo_column"" | db.execute >> "$LOGFILE" 2>&1
fi
done < "$TMPFILE1"

#we already inserted the geometry so we will recopy it in the newly created geometry column 
echo "Create geometry column" >> "$LOGFILE"
echo "ALTER TABLE "$GIS_OPT_OUTPUT" RENAME COLUMN "$geometry_column" TO the_geom_tmp" | db.execute >> "$LOGFILE" 2>&1
echo "SELECT AddGeometryColumn('', '"$GIS_OPT_OUTPUT"','"$geometry_column"',"$srid",'"$type"',"$coord_dimension");" | db.select >> "$LOGFILE" 2>&1
echo "UPDATE "$GIS_OPT_OUTPUT" SET "$geometry_column"=the_geom_tmp" | db.execute >> "$LOGFILE" 2>&1
echo "ALTER TABLE "$GIS_OPT_OUTPUT" DROP COLUMN the_geom_tmp" | db.execute >> "$LOGFILE" 2>&1
if [ "$GIS_FLAG_G" -eq 1 ] ; then
	#we add a gist index
	echo "CREATE INDEX "$GIS_OPT_OUTPUT"_index ON "$GIS_OPT_OUTPUT" USING GIST ("$geometry_column" GIST_GEOMETRY_OPS);" | db.execute >> 	"$LOGFILE" 2>&1
fi
if [ $? -ne 0 ] ; then
	echo "ERROR: an error occured during geometry insertion." 1>&2
	scripterror
fi

#now we are ready to achieve the dump with v.in.ogr
#first, retrieve the connection parameters
#sed -i option (original file replacement) is not implemented yet for msys (wingrass) so we use two files
#host and db :
db.connect -p > "$TMPFILE1"
#keep only the database ligne
sed '/^database/!d' "$TMPFILE1" > "$TMPFILE2"
#retrieve host and db values for v.in.ogr dsn argument
host=$(awk -F "," '{print $1}' "$TMPFILE2" | sed 's/database://')
db=$(awk -F "," '{print $2}' "$TMPFILE2")

#login and password
#login file can contain many line so we must look for the one corresponding to the database we are connected to
cat "$grassloginfile" > "$TMPFILE1"
#space after "$db" is important is there are two lines in login file with similar db names
sed -n "/pg "$host","$db" /p" "$TMPFILE1" > "$TMPFILE2"
user=$(awk -F " " '{print $3}' "$TMPFILE2")
password=$(awk -F " " '{print $4}' "$TMPFILE2")
if [ $? -ne 0 ] ; then
	echo "ERROR: sed was not able to retrieve your connection parameters from file." 1>&2
	scripterror
fi

#uncomment to check parameters in logfile :
#echo "connection parameters : " >> "$LOGFILE"
#echo "$host" >> "$LOGFILE"
#echo "$db" >> "$LOGFILE"
#echo "user="$user"" >> "$LOGFILE"
#echo "password="$password"" >> "$LOGFILE"

#now prepare the options
#-t option of v.in.ogr is dependant on -d flag : if the result table is keeped in postgresql, attributes don't have to be copied
if [ "$GIS_FLAG_D" -eq 1 ] ; then
	notable=""
	outputname=tmpoutput
	#we must shift to the dbf driver
	eval `g.gisenv`
	mkdir -p "$GISDBASE"/"$LOCATION_NAME"/"$MAPSET"/dbf/ >> "$LOGFILE" 2>&1
	db.connect driver=dbf database='$GISDBASE/$LOCATION_NAME/$MAPSET/dbf/' >> "$LOGFILE" 2>&1
else
	notable="-t"
	outputname="$GIS_OPT_OUTPUT"
fi
#-o option of v.in.ogr ; flag -o doesn't seem to work
if [ "$GIS_FLAG_R" -eq 1 ] ; then
	overrideprojection="-o"
else
	overrideprojection=""
fi

#ready to call v.in.ogr now
#Important : v.in.ogr outputs on stderr !
#redirect stderr to file
echo "call v.in.ogr" >> "$LOGFILE"
dsn="PG:"$host" "$db" user="$user" password="$password""
echo "dsn=$dsn" >> "$LOGFILE"

v.in.ogr $notable $overrideprojection dsn="$dsn" output="$outputname" layer="$GIS_OPT_OUTPUT" >> "$LOGFILE" 2>&1
if [ $? -ne 0 ] ; then
	echo "ERROR: an error occurred during v.in.ogr execution. Verify your connection parameters and ensure you used db.connect before launching this script. The -o flag may be necessary." 1>&2
	#reconnect to pg to be able to remove the table
	db.connect database=""$host","$db"" driver=pg
	scripterror
fi

echo "post-import operations" >> "$LOGFILE"
#if we import to grass dbf format, we must delete temporary postgresql table and rename the dbf layer to match the given output name
if [ "$GIS_FLAG_D" -eq 1 ] ; then
	g.rename vect=$outputname,$GIS_OPT_OUTPUT >> "$LOGFILE" 2>&1
	db.connect database=""$host","$db"" driver=pg
	echo "DROP TABLE "$GIS_OPT_OUTPUT"" | db.execute >> "$LOGFILE" 2>&1
#else we work directly with postgis so the connection between imported grass layer and postgres attribute table must be explicit
else
	v.db.connect -o map="$GIS_OPT_OUTPUT" table="$GIS_OPT_OUTPUT" >> "$LOGFILE" 2>&1
fi
#delete temporary data in geometry_columns table
echo "DELETE FROM geometry_columns WHERE f_table_name = '"$GIS_OPT_OUTPUT"'" | db.execute >> "$LOGFILE" 2>&1
if [ $? -ne 0 ] ; then
	echo "ERROR: error in post-import operation. Try to remove manually the postgis temp table (-d option) or set manually the connection between the layer and the table with v.db.connect." 1>&2
fi

scriptsuccess
