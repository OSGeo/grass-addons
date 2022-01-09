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
# PURPOSE:      Calculation of contiguous stream-specific variables that account 
#				for the upstream environment (based on r.stream.watersheds).
#
# COPYRIGHT:    (C) 2001-2012 by the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

#%Module
#% description: Calculation of contiguous stream-specific variables that account for the upstream environment (based on r.stream.watersheds).
#% keyword: raster
#% keyword: stream
#% keyword: drainage
#% keyword: hydrology
#%End

#%option
#% key: variable
#% type: string
#% key_desc: name
#% description: Name of raster to be converted into a stream-specific variable
#% required : yes
#%end

#%option
#% key: area
#% type: string
#% key_desc: string
#% multiple: no
#% options: watershed,stream
#% description: Area of aggregation: across the sub-watersheds or only across sub-streams
#% required : yes
#%end

#%option
#% key: folder 
#% type: string
#% key_desc: name
#% description: Provide the full folder path (same as for r.stream.watersheds)
#% required:no
#% answer: GISDBASE/folder_structure
#%end

#%option
#% key: out_folder 
#% type: string
#% key_desc: name
#% description: Provide the full folder path for the output stream-specific variable
#% required:no
#% answer: GISDBASE/stream-specific_variables
#%end

#%option
#% key: output
#% type: string
#% key_desc: method
#% multiple: yes
#% options: cells,min,max,range,mean,stddev,coeff_var,sum
#% label: Provide the output aggregation method for the stream-specific variable
#% description: upstream cells numbers, minimum, maximum, range, mean, standard deviation, coefficient of variation, sum. Output datatype is Int32
#% required:yes
#%end

#%option
#% key: scale
#% type: double
#% key_desc: value
#% label: Provide a scale factor to multiply or divide the final stream-specific variable
#% description: Provide it e.g. if input raster values are between -1 and 1, use scale=1000 to inicrease the number of decimals - all outputs will be rounded to integers 
#% answer: 1
#% required:no
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

if [ -z "$GIS_OPT_VARIABLE"  ] ; then
    g.message "Please provide the name of raster to be converted into a stream-specific variable."
exit 1
fi

if [ -z "$GIS_OPT_AREA" ] ; then
    g.message "Please provide area of aggregation: across the sub-watersheds or only across sub-streams."   
exit 1
fi

if [ -z "$GIS_OPT_OUTPUT"  ] ; then
    g.message "Please provide the output aggregation method for the stream-specific variable: upstream  min, max, range, mean, stddev, coeff_var, sum"
exit 1
fi

#check if drainage and stream file exists
eval `g.findfile element=cell file="$GIS_OPT_VARIABLE"`
if [ ! "$file" ] ; then
    g.message -e "<$GIS_OPT_VARIABLE> does not exist! Aborting."
    exit 1
fi


export GISDBASE=$(g.gisenv get=GISDBASE  separator=space)
export LOCATION_NAME=$(g.gisenv get=LOCATION_NAME  separator=space)
export GIS_OPT_AREA
export GIS_OPT_VARIABLE
export GIS_OPT_OUTPUT
export GIS_OPT_SCALE

if [ ${GIS_OPT_FOLDER} = "GISDBASE/folder_structure" ] ; then
       export GIS_OPT_FOLDER=$GISDBASE"/folder_structure"
else 
       export GIS_OPT_FOLDER=$GIS_OPT_FOLDER
fi

if [ ${GIS_OPT_OUT_FOLDER} = "GISDBASE/stream-specific_variables" ] ; then
      export GIS_OPT_OUT_FOLDER=$GISDBASE"/stream-specific_variables"
else 
      export GIS_OPT_OUT_FOLDER=$GIS_OPT_OUT_FOLDER
fi

mkdir  $GIS_OPT_OUT_FOLDER  2> /dev/null 

# what to do in case of user break:
exitprocedure()
{
echo ""
g.message -e 'Process aborted by user. All intermediate files have been deleted!'

# reset in the permanent mapset 
g.gisenv set="MAPSET=PERMANENT"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="GISDBASE=$GISDBASE"

# delete intermediate files 
rm -fr  $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}* 
find    $GIS_OPT_FOLDER/ -maxdepth 1 -name  '*.txt' -delete 
find    $GIS_OPT_FOLDER/ -maxdepth 1 -name  '*.tif' -delete 
rm -fr  $GIS_OPT_FOLDER/blockfile/stat_*.txt 

exit 1
}

# shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 9 15 19

echo ""
echo "##########################################################################"
echo "Stream-specific variable calculation based on the sub-watersheds and sub-streams"
echo ""
echo "Citation: Domisch, S., Amatulli, G., Jetz, W. (in review)"
echo "Near-global freshwater-specific environmental variables for"
echo "biodiversity analyses in 1km resolution. Scientific Data"
echo "##########################################################################"
echo ""

export GISRC_def=$GISRC

rm -fr   $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}*

echo Using  $( ls $GIS_OPT_FOLDER/blockfile/blockfile* | wc -l ) blocks in  $GIS_OPT_FOLDER/blockfile/

for file in  $GIS_OPT_FOLDER/*digit4/*digit3/*digit2/*digit1/blockfile*_sub_${GIS_OPT_AREA}.tar.gz    ; do 
    
    export DIRNAME=$(dirname   $file )
    filename=$(basename $file )
    cd $DIRNAME
    tar -xf $file 
    cd $GISDBASE

    export BLKID=$(echo $filename |  awk -v GIS_OPT_AREA=${GIS_OPT_AREA} '{ gsub("0000", "") ; gsub("blockfile","") ; gsub("_sub_","") ; gsub("GIS_OPT_AREA","") ; gsub(".tar.gz","") ;  print  }')
    export dir4d=${BLKID: -4:1} ; if [ -z $dir4d  ] ; then  dir4d=0 ; fi
    export dir3d=${BLKID: -3:1} ; if [ -z $dir3d  ] ; then  dir3d=0 ; fi  
    export dir2d=${BLKID: -2:1} ; if [ -z $dir2d  ] ; then  dir2d=0 ; fi
    export dir1d=${BLKID: -1:1} ; if [ -z $dir1d  ] ; then  dir1d=0 ; fi

g.gisenv set="GISDBASE=$GISDBASE"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="MAPSET=PERMANENT"

echo  "Start the stream-specific variable aggregation for block $file"

ls  $DIRNAME/sub_${GIS_OPT_AREA}ID*.tif | awk '{ if (NR>0) { print $1 ,  NR} }'   | xargs  -n 2 -P $GIS_OPT_CPU  bash -c  $' 

file=$1
filename=$(basename $file .tif )
if [  $GIS_OPT_AREA =  "watershed"  ] ; then ID=${filename:15:99}; fi 
if [  $GIS_OPT_AREA =  "stream"  ] ; then ID=${filename:12:99}; fi 

NR=$2

if [ $( expr  $( expr $NR + 1 ) / 100)  -eq  $( expr $NR / 100 + 1 ) ] ; then 
echo  -en  "\r$(expr $NR / 100 + 1 )% done"
fi

# replicate the start-GISRC in a uniq GISRC

cp   $GISRC_def    $HOME/.grass8/rc$ID
export GISRC=$HOME/.grass8/rc$ID

g.mapset  -c   mapset=sub_${GIS_OPT_AREA}ID$ID   location=$LOCATION_NAME  dbase=$GISDBASE   --quiet

rm -f    $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}ID$ID/.gislock      

export GISBASE=$( grep  gisbase   $(which grass) | awk \'{ if(NR==2) { gsub ("\\"","" ) ; print $3 }  }\' )
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH="$GISBASE/lib"
export GRASS_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PYTHONPATH="$GISBASE/etc/python:$PYTHONPATH"
export MANPATH=$MANPATH:$GISBASE/man

# echo  Load $DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif 

r.in.gdal input=$DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif       output=sub_${GIS_OPT_AREA}ID${ID}   --q 

g.region   rast=sub_${GIS_OPT_AREA}ID${ID}@sub_${GIS_OPT_AREA}ID${ID}  zoom=sub_${GIS_OPT_AREA}ID${ID}@sub_${GIS_OPT_AREA}ID${ID} --q 
r.mapcalc "sub_$GIS_OPT_VARIABLE = if ( sub_${GIS_OPT_AREA}ID${ID} == 1 , $GIS_OPT_VARIABLE@PERMANENT  , null())"    --o --q

echo $ID"|"$( r.univar -t --q  map=sub_$GIS_OPT_VARIABLE  |  awk  \'{ if (NR==2 ) print}\'   ) >   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt

FULL=$(awk -F "|"  \'{if (NF==13) {print 1 } else {print 0} }\'   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt)

if [ $FULL -eq 0 ] ; then 
rm   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt   
else
rm -f $DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif      
fi

rm -r $HOME/.grass8/rc$ID    $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}ID$ID

' _ 

g.gisenv set="MAPSET=PERMANENT"
g.gisenv set="LOCATION_NAME=$LOCATION_NAME"
g.gisenv set="GISDBASE=$GISDBASE"

echo -en  "\r100% done"
echo ""

echo "Check for missing files due to RAM overload"

if ls $DIRNAME/sub_${GIS_OPT_AREA}ID*.tif  1> /dev/null 2>&1 ; then

echo $(ls $DIRNAME/sub_${GIS_OPT_AREA}ID*.tif  | wc -l ) files had RAM issues

ls $DIRNAME/sub_${GIS_OPT_AREA}ID*.tif  | awk '{ if (NR>0) { print $1 ,  NR} }'   | xargs  -n 2 -P 1 bash -c  $' 

file=$1
filename=$(basename $file .tif )

echo Fix missing file $file using only 1 CPU

if [  $GIS_OPT_AREA =  "watershed"  ] ; then ID=${filename:15:99}; fi 
if [  $GIS_OPT_AREA =  "stream"  ] ; then ID=${filename:12:99}; fi 

NR=$2

if [ ! -f  $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt ] ; then 

if [ $( expr  $( expr $NR + 1 ) / 100)  -eq  $( expr $NR / 100 + 1 ) ] ; then 
echo  -en  "\r$(expr $NR / 100 + 1 )% done"
fi

# replicate the start-GISRC in a uniq GISRC

cp   $GISRC_def    $HOME/.grass8/rc$ID
export GISRC=$HOME/.grass8/rc$ID

g.mapset  -c   mapset=sub_${GIS_OPT_AREA}ID$ID   location=$LOCATION_NAME  dbase=$GISDBASE   --quiet

rm -f    $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}ID$ID/.gislock      

export GISBASE=$( grep  gisbase   $(which grass) | awk \'{ if(NR==2) { gsub ("\\"","" ) ; print $3 }  }\' )
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH="$GISBASE/lib"
export GRASS_LD_LIBRARY_PATH="$LD_LIBRARY_PATH"
export PYTHONPATH="$GISBASE/etc/python:$PYTHONPATH"
export MANPATH=$MANPATH:$GISBASE/man

# echo  Load $DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif 

r.in.gdal input=$DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif       output=sub_${GIS_OPT_AREA}ID${ID}   --q 
rm -f $DIRNAME/sub_${GIS_OPT_AREA}ID${ID}.tif 

g.region   rast=sub_${GIS_OPT_AREA}ID${ID}@sub_${GIS_OPT_AREA}ID${ID}  zoom=sub_${GIS_OPT_AREA}ID${ID}@sub_${GIS_OPT_AREA}ID${ID} --q 
r.mapcalc "sub_$GIS_OPT_VARIABLE = if ( sub_${GIS_OPT_AREA}ID${ID} == 1 , $GIS_OPT_VARIABLE@PERMANENT  , null())"    --o --q

echo $ID"|"$( r.univar -t --q  map=sub_$GIS_OPT_VARIABLE  |  awk  \'{ if (NR==2 ) print}\'   ) >   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt

FULL=$(awk -F "|"  \'{if (NF==13) {print 1 } else {print 0} }\'   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt)

if [ $FULL -eq 0 ] ; then rm   $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID$ID.txt ; fi

rm -r $HOME/.grass8/rc$ID    $GISDBASE/$LOCATION_NAME/sub_${GIS_OPT_AREA}ID$ID

fi 

' _ 

else 
echo 0 files had RAM issues
fi 


cat $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID*.txt >  $DIRNAME/stat_${GIS_OPT_VARIABLE}.txt 
rm -f  $DIRNAME/stat_${GIS_OPT_VARIABLE}_ID*.txt 

done 

echo "Aggregating the final table to reclassify the raster ID"

echo "ID|non_null_cells|null_cells|min|max|range|mean|mean_of_abs|stddev|variance|coeff_var|sum|sum_abs" >  $GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}.txt
cat  $GIS_OPT_FOLDER/*digit4/*digit3/*digit2/*digit1/stat_${GIS_OPT_VARIABLE}.txt  >>  $GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}.txt
rm -f  $GIS_OPT_FOLDER/*digit4/*digit3/*digit2/*digit1/stat_${GIS_OPT_VARIABLE}.txt

echo Reclass the grid_id for the following output  ${GIS_OPT_OUTPUT//","/" "}

echo ${GIS_OPT_OUTPUT//","/" "} |  xargs -n 1 -P $GIS_OPT_CPU bash -c $'

if [ $1 = "cells" ]     ; then col=2 ; fi
if [ $1 = "min" ]       ; then col=4 ; fi
if [ $1 = "max" ]       ; then col=5 ; fi
if [ $1 = "range" ]     ; then col=6 ; fi
if [ $1 = "mean" ]      ; then col=7 ; fi 
if [ $1 = "stddev" ]    ; then col=9 ; fi 
if [ $1 = "coeff_var" ] ; then col=11 ; fi 
if [ $1 = "sum" ]       ; then col=12 ; fi 

awk -F "|" -v col=$col -v scale=$GIS_OPT_SCALE  \' { if (NR>1 ) {gsub("-nan","0",$col); gsub("inf","0",$col);  print $1" = "int($col * scale) }}\' $GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}.txt  > $GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}_$1.txt

' _ 

echo ${GIS_OPT_OUTPUT//","/" "} |  xargs -n 1 -P 1 bash -c $'

if [ $1 = "cells" ]     ; then col=2 ; fi
if [ $1 = "min" ]       ; then col=4 ; fi 
if [ $1 = "max" ]       ; then col=5 ; fi 
if [ $1 = "range" ]     ; then col=6 ; fi 
if [ $1 = "mean" ]      ; then col=7 ; fi 
if [ $1 = "stddev" ]    ; then col=9 ; fi 
if [ $1 = "coeff_var" ] ; then col=11 ; fi 
if [ $1 = "sum"  ]      ; then col=12 ; fi 

echo  Create stream-specific variable:  $GIS_OPT_VARIABLE $1

r.reclass input=grid_ID  output=${GIS_OPT_VARIABLE}_$1  rules=$GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}_${1}.txt   --overwrite   --q
# rm -f $GIS_OPT_FOLDER/blockfile/stat_${GIS_OPT_VARIABLE}_${1}.txt

r.mapcalc "  ${GIS_OPT_VARIABLE}_$1  = ${GIS_OPT_VARIABLE}_$1 "  --o  

r.out.gdal -c  input=${GIS_OPT_VARIABLE}_${1}  nodata=-9999  output=$GIS_OPT_OUT_FOLDER/${GIS_OPT_VARIABLE}_${1}.tif  type=Int32  -c  createopt="COMPRESS=LZW,ZLEVEL=9"  --o --q  2> /dev/null
if test -f "$GIS_OPT_FOLDER/blockfile/${GIS_OPT_VARIABLE}_${1}.tif"; then echo "$GIS_OPT_FOLDER/blockfile/${GIS_OPT_VARIABLE}_${1}.tif has been created!";fi
#echo "$GIS_OPT_OUT_FOLDER/blockfile/${GIS_OPT_VARIABLE}_${1}.tif has been created!"

' _ 

exit 

echo "The full stream variable calculation has been done!"
echo "To list the stream-specific output variables: ls $GIS_OPT_OUT_FOLDER/*.tif"
