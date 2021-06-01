#!/bin/sh
#
############################################################################
#
# MODULE:	r.roughness.window.vector.sh
# AUTHOR(S):	Carlos H. Grohmann <carlos dot grohmann at gmail dot com >
# PURPOSE:	Calculates surface roughness from DEMs.
#		In this script surface roughness is taken as the dispersion
#		of vectors normal to surface areas (pixels). Normal vectors
#		are defined by slope and aspect.
#		Reference:
#		Hobson, R.D., 1972. Surface roughness in topography: 
#		quantitative approach. In: Chorley, R.J. (ed) Spatial 
#		analysis in geomorphology. Methuer, London, p.225-245.
#
#		This script will create several temporary maps, for the
#		directional cosines in each direction (x,y,z), for the sum
#		of these cosines and vector strengh.
#
#		If the user does not specify the output map name, it will be
#		set to INPUT_MAP_roughness_vector_NxN
#		where N is the window size.
#
# COPYRIGHT:	(C) 2007 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#% description: Calculates surface roughness with a moving-window approach
#%End
#%option
#% key: map
#% gisprompt: old,cell,raster
#% type: string
#% description: Input raster elevation map
#% required : yes
#%end
#%option
#% key: slope
#% gisprompt: old,cell,raster
#% type: string
#% description: Input raster slope map
#% required : yes
#%end
#%option
#% key: aspect
#% gisprompt: old,cell,raster
#% type: string
#% description: Input raster aspect map
#% required : yes
#%end
#%option
#% key: window
#% type: integer
#% description: Window size (3,5,7,...,25)
#% required : no
#% answer : 3
#%end
#%option
#% key: strength
#% gisprompt: old,cell,raster
#% type: string
#% description: Output vector strength map 
#% required : no
#%end
#%option
#% key: fisher
#% gisprompt: old,cell,raster
#% type: string
#% description: Output Fischer's K parameter map 
#% required : no
#%end
#%option
#% key: compass
#% gisprompt: old,cell,raster
#% type: string
#% description: OPTIONAL: Compass aspect values (longitude)
#% required : no
#%end
#%option
#% key: colatitude
#% gisprompt: old,cell,raster
#% type: string
#% description: OPTIONAL: Colatitude values (90 - slope)
#% required : no
#%end
#%option
#% key: xcos
#% gisprompt: old,cell,raster
#% type: string
#% description: OPTIONAL: X directional cosine map
#% required : no
#%end
#%option
#% key: ycos
#% gisprompt: old,cell,raster
#% type: string
#% description: OPTIONAL: Y directional cosine map
#% required : no
#%end
#%option
#% key: zcos
#% gisprompt: old,cell,raster
#% type: string
#% description: OPTIONAL: Z directional cosine map
#% required : no
#%end
#
if test "$GISBASE" = ""; then
 echo "You must be in GRASS GIS to run this program." >&2
 exit 1
fi   

# save command line
if [ "$1" != "@ARGS_PARSED@" ] ; then
    CMDLINE="`basename $0`"
    for arg in "$@" ; do
        CMDLINE="$CMDLINE \"$arg\""
    done
    export CMDLINE
    exec g.parser "$0" "$@"
fi
PROG=`basename $0`

# setting environment, so that awk works properly in all languages
unset LC_ALL
LC_NUMERIC=C
export LC_NUMERIC

eval `g.gisenv`
: ${GISBASE?} ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION=$GISDBASE/$LOCATION_NAME/$MAPSET

program=`basename $0`

map=$GIS_OPT_MAP
slope=$GIS_OPT_SLOPE
aspect=$GIS_OPT_ASPECT
window=$GIS_OPT_WINDOW


#check if input file exists

eval `g.findfile element=cell file=$map`
if [ -z "$name" ] ; then
   g.message -e  "Map <$map> not found! Aborting."
   exit 1
fi

eval `g.findfile element=cell file=$slope`
if [ -z "$name" ] ; then
   g.message -e  "Map <$slope> not found! Aborting."
   exit 1
fi

eval `g.findfile element=cell file=$aspect`
if [ -z "$name" ] ; then
   g.message -e  "Map <$aspect> not found! Aborting."
   exit 1
fi

if [ -z "$GIS_OPT_STRENGTH" ]; then
    STRENGTH="${map%%@*}_vector_strength_${window}x${window}"
else
    STRENGTH="$GIS_OPT_STRENGTH"
fi

if [ -z "$GIS_OPT_FISHER" ]; then
    FISHER="${map%%@*}_fisher_K_${window}x${window}"
else
    FISHER="$GIS_OPT_FISHER"
fi

#######################################################################
# what to do in case of user break:
exitprocedure()
{
 g.message -e 'User break!'
 #delete any TMP files:
 g.remove rast=$TMP1,$TMP3,$TMP4,$TMP5,$TMP6,$TMP7,$TMP8 > /dev/null

}
# shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 15


#######################################################################
#some temp rasters:

TMP6=sum_dir_cosine_x_$$
TMP7=sum_dir_cosine_y_$$
TMP8=sum_dir_cosine_z_$$

#correct aspect angles from cartesian (GRASS default) to compass angles
#   if(A==0,0,if(A < 90, 90-A, 360+90-A))
if [ -z "$GIS_OPT_COMPASS" ]; then
    echo "Calculating compass aspect values (longitude)"
    TMP1=aspect_compass_$$
    r.mapcalc $TMP1 = "if($aspect==0,0,if($aspect < 90, 90-$aspect, 360+90-$aspect))"
else
    echo "Using previous calculated compass aspect values (longitude)"
    TMP1="$GIS_OPT_COMPASS"
fi

#Calculates colatitude (90-slope)
if [ -z "$GIS_OPT_COLATITUDE" ]; then
   echo "Calculating colatitude (90-slope)"
   TMP2=normal_angle_$$
   r.mapcalc $TMP2 = "90 - $slope"
else
    echo "Using previous calculated colatitude values"
    TMP2="$GIS_OPT_COLATITUDE"
fi

#direction cosines relative to axis oriented north, east and up
#direction cosine calculation according to McKean & Roering (2004), Geomorphology, 57:331-351.

if [ -z "$GIS_OPT_XCOS" ]; then
echo "Calculating X direction cosine"
    TMP3=dir_cosine_x_$$
    r.mapcalc $TMP3 = "sin($TMP2)*cos($TMP1)"
else
    echo "Using previous calculated X directional cosine values"
    TMP3="$GIS_OPT_XCOS"
fi

if [ -z "$GIS_OPT_YCOS" ]; then
echo "Calculating Y direction cosine"
    TMP4=dir_cosine_y_$$
    r.mapcalc $TMP4 = "sin($TMP2)*sin($TMP1)"
else
    echo "Using previous calculated Y directional cosine values"
    TMP4="$GIS_OPT_YCOS"
fi

if [ -z "$GIS_OPT_ZCOS" ]; then
echo "Calculating Z direction cosine"
    TMP5=dir_cosine_z_$$
    r.mapcalc $TMP5 = "cos($TMP2)"
else
    echo "Using previous calculated Z directional cosine values"
    TMP5="$GIS_OPT_ZCOS"
fi  


echo "Calculating sum of X direction cosines"
r.neighbors input=$TMP3 output=$TMP6 method=sum size=$window --overwrite

echo "Calculating sum of Y direction cosines"
r.neighbors input=$TMP4 output=$TMP7 method=sum size=$window --overwrite

echo "Calculating sum of Z direction cosines"
r.neighbors input=$TMP5 output=$TMP8 method=sum size=$window --overwrite

echo "Calculating vector strength"
r.mapcalc $STRENGTH = "sqrt(exp($TMP6,2) + exp($TMP7,2) + exp($TMP8,2))"


echo "Calculating Inverted Fisher's K parameter"
# k=1/((N-1)/(N-R))
r.mapcalc $FISHER = "($window * $window - $STRENGTH) / ($window * $window - 1)"

#cleanup
g.remove rast=$TMP6,$TMP7,$TMP8 > /dev/null

if [ -z "$GIS_OPT_COMPASS" ]; then
g.remove rast=$TMP1 > /dev/null
fi

if [ -z "$GIS_OPT_COLATITUDE" ]; then
g.remove rast=$TMP2 > /dev/null
fi

if [ -z "$GIS_OPT_XCOS" ]; then
g.remove rast=$TMP3 > /dev/null
fi

if [ -z "$GIS_OPT_YCOS" ]; then
g.remove rast=$TMP4 > /dev/null
fi

if [ -z "$GIS_OPT_ZCOS" ]; then
g.remove rast=$TMP5 > /dev/null
fi

echo ""
if [ -n "$GIS_OPT_STRENGTH" ] ; then
    echo "Surface roughness map created and named [$STRENGTH]."
else
    echo "Surface roughness map created and named [$STRENGTH]. Consider renaming."
fi

echo ""
if [ -n "$GIS_OPT_FISHER" ] ; then
    echo "Surface roughness map created and named [$FISHER]."
else
    echo "Surface roughness map created and named [$FISHER]. Consider renaming."
fi

echo "Done."
exit 0
