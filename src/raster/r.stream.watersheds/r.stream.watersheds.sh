#!/bin/bash
#
############################################################################
#
# MODULE:       r.stream.watersheds
#
# AUTHOR(S):    Giuseppe Amatulli & Sami Domisch
#               based on "Domisch, S., Amatulli, G., Jetz, W. (in review) 
#				Near-global freshwater-specific environmental variables for 
# 				biodiversity analyses in 1km resolution. Scientific Data"
#
# PURPOSE:      Delineate the upstream contributing area ('sub-watershed') and 
#				stream sections ('sub-stream') for each grid cell of a 
#				stream network
#
# COPYRIGHT:    (C) 2001-2012 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Sub-watershed and sub-stream delineation based on the drainage direction and a gridded stream network.
#% keyword: raster
#% keyword: stream
#% keyword: drainage
#% keyword: hydrology
#%End

#%option
#% key: drainage
#% type: string
#% key_desc: name
#% description: Name of the drainage direction raster (generated with r.watershed)
#% required : yes
#%end

#%option
#% key: stream
#% type: string
#% key_desc: name
#% description: Name of the stream network raster
#% required : yes
#%end

#%option
#% key: folder 
#% type: string
#% key_desc: name
#% description: Provide the full folder path and name where the sub-watersheds and sub-streams should be stored
#% required:no
#% answer: GISDBASE/folder_structure
#%end

#%option
#% key: cpu
#% type: double
#% description: Number of CPUs used for the parallel computation
#% answer: 1
#% required:no
#%end

if [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." >&2
    exit 1
fi

if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi

#### check if we have awk
if [ ! -x "`which awk`" ] ; then
    g.message -e "awk required, please install awk or gawk first"
    exit 1
fi

# setting environment, so that awk works properly in all languages
unset LC_ALL
LC_NUMERIC=C
export LC_NUMERIC

#test:

if [ -z "$GIS_OPT_DRAINAGE"  ] ; then
    g.message "Please provide the name of the drainage direction raster."
exit 1
fi

if [ -z "$GIS_OPT_STREAM" ] ; then
    g.message "Please provide the name of the stream network raster."
exit 1
fi

#check if drainage and stream file exists
eval `g.findfile element=cell file="$GIS_OPT_STREAM"`
if [ ! "$file" ] ; then
    g.message -e "<$GIS_OPT_STREAM> does not exist! Aborting."
    exit 1
fi

eval `g.findfile element=cell file="$GIS_OPT_DRAINAGE"`
if [ ! "$file" ] ; then
    g.message -e "<$GIS_OPT_DRAINAGE> does not exist! Aborting."
    exit 1
fi

export GISDBASE=$(g.gisenv get=GISDBASE  separator=space)
export LOCATION_NAME=$(g.gisenv get=LOCATION_NAME  separator=space)
export GIS_OPT_STREAM
export GIS_OPT_DRAINAGE
export GIS_OPT_CPU

if [ ${GIS_OPT_FOLDER} = "GISDBASE/folder_structure" ] ; then
       export GIS_OPT_FOLDER=$GISDBASE"/folder_structure"
else 
       export GIS_OPT_FOLDER=$GIS_OPT_FOLDER
fi

# what to do in case of user break:
exitprocedure()
{
echo ""
g.message -e 'Process aborted by user. All intermediate files have been deleted!'

# reset in the permanent mapset 
g.gisenv set="MAPSET=PERMANENT"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="GISDBASE=$GISDBASE"

# delete folder structure and sub-watershed  mapset
rm -fr   $GIS_OPT_FOLDER   $GISDBASE/$LOCATION_NAME/sub_watershedID*

exit 1 
}

# shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 15

echo ""
echo "#######################################################################################################"
echo "Sub-watershed and sub-stream delineation based on the drainage direction and a gridded stream network."
echo ""
echo "Citation: Domisch, S., Amatulli, G., Jetz, W. (in review)"
echo "Near-global freshwater-specific environmental variables for"
echo "biodiversity analyses in 1km resolution. Scientific Data"
echo "#######################################################################################################"
echo ""
echo Exporting stream grid cell coordinates and saving in $GIS_OPT_FOLDER/stream_coord_lines.txt

rm -fr    $GIS_OPT_FOLDER 2> /dev/null
mkdir     $GIS_OPT_FOLDER 2> /dev/null

r.out.xyz   --o input=$GIS_OPT_STREAM  separator=space   output=$GIS_OPT_FOLDER/stream_coord.txt  --q

awk 'BEGIN {print "X","Y","ID"} { print $1, $2 ,  NR  }' $GIS_OPT_FOLDER/stream_coord.txt >   $GIS_OPT_FOLDER/stream_coord_lines.txt

echo  Create the raster ID file

v.in.ascii  --overwrite  input=$GIS_OPT_FOLDER/stream_coord_lines.txt   output=vector_ID   x=1  y=2  separator=' '  skip=1 --q  2> /dev/null

echo Rasterize the stream network point coordinates

v.to.rast --overwrite  input=vector_ID   output=grid_ID   layer=vector_ID     use=attr     attrcolumn=cat   type=point  --q 

echo  Create the folder structure in $GIS_OPT_FOLDER/ to save results

# build up folder structure for all the digit bigger than 9999.
# from     0 to 9999  goes in the /0digit4/0digit3/0digit2/0digit1/
# from 10000 to 19999 goes in the /0digit4/0digit3/0digit2/1digit1/

max_line=$(wc -l  $GIS_OPT_FOLDER/stream_coord.txt | awk '{  print $1 }' )
max_seq1d=${max_line: -5:1} ; if [ -z $max_seq1d ] ; then max_seq1d=0 ; fi 
max_seq2d=${max_line: -6:1} ; if [ -z $max_seq2d ] ; then max_seq2d=0 ; else  max_seq1d=9 ; fi 
max_seq3d=${max_line: -7:1} ; if [ -z $max_seq3d ] ; then max_seq3d=0 ; else  max_seq2d=9 ; max_seq1d=9 ; fi 
max_seq4d=${max_line: -8:1} ; if [ -z $max_seq4d ] ; then max_seq4d=0 ; else  max_seq3d=9 ; max_seq2d=9 ; max_seq1d=9 ; fi 

for dir4d in  $(seq 0 $max_seq4d) ; do
    for dir3d in  $(seq 0 $max_seq3d) ; do
	for dir2d in  $(seq 0 $max_seq2d) ; do
	    for dir1d in  $(seq 0 $max_seq1d) ; do
		mkdir -p  $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1
	    done
	done
    done 
done 

mkdir  $GIS_OPT_FOLDER/blockfile

echo  "Split the stream grid cell coordinate file with $( wc -l $GIS_OPT_FOLDER/stream_coord.txt  | awk '{ print $1 }' ) grid cells into blocks of 10000 cells"

awk -v PATH=$GIS_OPT_FOLDER 'NR%10000==1{x=PATH"/blockfile/blockfile"(++i*10000-10000)}{print > x}'  $GIS_OPT_FOLDER/stream_coord_lines.txt

awk '{ if(NR>1) print  }' $GIS_OPT_FOLDER/blockfile/blockfile0 > $GIS_OPT_FOLDER/blockfile/blockfile0_tmp
mv $GIS_OPT_FOLDER/blockfile/blockfile0_tmp $GIS_OPT_FOLDER/blockfile/blockfile0

echo Create $( ls $GIS_OPT_FOLDER/blockfile/blockfile* | wc -l ) subsets: $GIS_OPT_FOLDER/blockfile/blockfile*.tif

rm -fr $GISDBASE/$LOCATION_NAME/sub_watershedID*

export GISRC_def=$GISRC

for file in $GIS_OPT_FOLDER/blockfile/blockfile* ; do 
    
    filename=$(basename $file )
    
    export BLKID=$(echo $filename | awk '{ gsub("0000", "") ; gsub("blockfile","") ; print  }')
    export dir4d=${BLKID: -4:1} ; if [ -z $dir4d  ] ; then  dir4d=0 ; fi  
    export dir3d=${BLKID: -3:1} ; if [ -z $dir3d  ] ; then  dir3d=0 ; fi    
    export dir2d=${BLKID: -2:1} ; if [ -z $dir2d  ] ; then  dir2d=0 ; fi  
    export dir1d=${BLKID: -1:1} ; if [ -z $dir1d  ] ; then  dir1d=0 ; fi  
    export file=$file

rm -f $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/*.tif 

g.region -d  rast=$GIS_OPT_DRAINAGE@PERMANENT

g.gisenv set="GISDBASE=$GISDBASE"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="MAPSET=PERMANENT"

echo  "Start the sub-watershed delineation for subset $file"

awk '{ print NR , $1 , $2 ,$3 }'   $file     | xargs  -n 4 -P $GIS_OPT_CPU  bash -c  $' 
NR=$1
X_coord=$2
Y_coord=$3
ID=$4


if [ $( expr  $( expr $NR + 1 ) / 100)  -eq  $( expr $NR / 100 + 1 ) ] ; then
echo  -en  "\r$(expr $NR / 100 + 1 )% done"
fi


# replicate the start-GISRC in a unique GISRC

cp   $GISRC_def    $HOME/.grass8/rc$ID
export GISRC=$HOME/.grass8/rc$ID

g.mapset  -c   mapset=sub_watershedID$ID   location=$LOCATION_NAME  dbase=$GISDBASE   --quiet

rm -f    $GISDBASE/$LOCATION_NAME/sub_watershedID$ID/.gislock      

export GISBASE=$( grep  gisbase   $(which grass70) | awk \'{ if(NR==2) { gsub ("\\"","" ) ; print $3 }  }\' )
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH="$GISBASE/lib"
export GRASS_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PYTHONPATH="$GISBASE/etc/python:$PYTHONPATH"
export MANPATH=$MANPATH:$GISBASE/man

r.water.outlet --o  --q  input=$GIS_OPT_DRAINAGE@PERMANENT  output=sub_watershedID$ID  coordinates=$X_coord,$Y_coord

g.region   rast=sub_watershedID${ID}@sub_watershedID${ID}  zoom=sub_watershedID${ID}@sub_watershedID${ID}
r.out.gdal -c type=Byte    --o --q     nodata=255     createopt="COMPRESS=LZW,ZLEVEL=9"    input=sub_watershedID$ID@sub_watershedID${ID}  output=$GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_watershedID$ID.tif

### Crop this basin template --> for temperature only for the stream cells in this basin

r.mapcalc  "sub_streamID${ID} = if ( sub_watershedID${ID}@sub_watershedID${ID}  == 1 & ${GIS_OPT_STREAM}@PERMANENT >= 1 , 1 , null()  )"   --o --q
r.null  map=sub_streamID${ID}  setnull=0    --q
r.out.gdal  -c type=Byte    --o --q     nodata=255     createopt="COMPRESS=LZW,ZLEVEL=9"   input=sub_streamID${ID}@sub_watershedID${ID}    output=$GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_streamID${ID}.tif 

if [ ! -f $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_streamID${ID}.tif  ] ; then the file $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_streamID${ID}.tif  dose not exist ; fi 

rm -r $HOME/.grass8/rc$ID    $GISDBASE/$LOCATION_NAME/sub_watershedID$ID

' _

echo -en  "\r100% done"

rm -fr    $GISDBASE/$LOCATION_NAME/sub_watershedID*

echo ""
echo  $(ls -l  $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_watershedID*.tif | wc -l ) sub-watersheds have been processed 

# reset mapset to PERMANENT 

g.gisenv set="MAPSET=PERMANENT"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="GISDBASE=$GISDBASE"

echo Check for missing files due to RAM overload

cat  $file  | xargs  -n 3 -P 1  bash -c  $'   

X_coord=$1
Y_coord=$2
ID=$3

if  [    !  -f  $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_watershedID$ID.tif ] ; then 

echo Fix missing file $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_watershedID$ID.tif using only 1 CPU

# replicate the start-GISRC in a unique GISRC

cp   $GISRC_def    $HOME/.grass8/rc$ID
export GISRC=$HOME/.grass8/rc$ID

g.mapset  -c   mapset=sub_watershedID$ID   location=$LOCATION_NAME  dbase=$GISDBASE   --quiet

rm -f    $GISDBASE/$LOCATION_NAME/sub_watershedID$ID/.gislock      

export GISBASE=$( grep  gisbase   $(which grass70) | awk \'{ if(NR==2) { gsub ("\\"","" ) ; print $3 }  }\' )
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH="$GISBASE/lib"
export GRASS_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PYTHONPATH="$GISBASE/etc/python:$PYTHONPATH"
export MANPATH=$MANPATH:$GISBASE/man

r.water.outlet --o  --q  input=$GIS_OPT_DRAINAGE@PERMANENT  output=sub_watershedID$ID  coordinates=$X_coord,$Y_coord

g.region   rast=sub_watershedID${ID}@sub_watershedID${ID}  zoom=sub_watershedID${ID}@sub_watershedID${ID}
r.out.gdal -c type=Byte    --o --q     nodata=255     createopt="COMPRESS=LZW,ZLEVEL=9"    input=sub_watershedID$ID@sub_watershedID${ID}  output=$GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_watershedID$ID.tif

### Crop this basin template --> for temperature only for the stream cells in this basin

r.mapcalc  "sub_streamID${ID} = if ( sub_watershedID${ID}@sub_watershedID${ID}  == 1 & ${GIS_OPT_STREAM}@PERMANENT >= 1 , 1 , null()  )"   --o --q
r.null  map=sub_streamID${ID}  setnull=0    --q
r.out.gdal  -c type=Byte    --o --q     nodata=255     createopt="COMPRESS=LZW,ZLEVEL=9"   input=sub_streamID${ID}@sub_watershedID${ID}    output=$GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/sub_streamID${ID}.tif 

rm -r $HOME/.grass8/rc$ID    $GISDBASE/$LOCATION_NAME/sub_watershedID$ID

fi

' _

rm -fr    $GISDBASE/$LOCATION_NAME/sub_watershedID*

echo "Compress the sub-watersheds and sub-streams to reduce the number of inodes filling up the hard disk"


cd $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/
	 	
tar -zcPf  ${filename}_sub_watershed.tar.gz  sub_watershedID*.tif
tar -zcPf  ${filename}_sub_stream.tar.gz     sub_streamID*.tif   
	
cd  $GIS_OPT_FOLDER

g.gisenv set="MAPSET=PERMANENT"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="GISDBASE=$GISDBASE"

rm -fr    $GISDBASE/$LOCATION_NAME/sub_watershedID* $GIS_OPT_FOLDER/${dir4d}digit4/${dir3d}digit3/${dir2d}digit2/${dir1d}digit1/*.tif

done 

echo "The full sub-watershed delineation process has been done!"
echo "To list the compressed files: ls $GIS_OPT_FOLDER/*digit4/*digit3/*digit2/*digit1/*.tar.gz"
echo  "Now you can use r.stream.variables to compute stream-specific environmental variables."
