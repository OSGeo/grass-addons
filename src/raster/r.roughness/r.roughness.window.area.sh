#!/bin/sh
#
############################################################################
#
# MODULE:	roughness.window.area.sh
# AUTHOR(S):	Carlos H. Grohmann <carlos dot grohmann at gmail dot com >
# PURPOSE:	Calculates surface roughness from DEMs. (uses r.surf.area)
#		In this script surface roughness is used in the sense of 
#		Hobson (1972), who describes it as the ratio between surface 
#		(real) area and flat (plan) area of square cells; in this 
#		approach, flat surfaces would present values close to 1, 
#		whilst in irregular ones the ratio shows a curvilinear 
#		relationship which asymptotically approaches infinity as the 
#		real areas increases.
#		Reference:
#		Hobson, R.D., 1972. Surface roughness in topography: 
#		quantitative approach. In: Chorley, R.J. (ed) Spatial 
#		analysis in geomorphology. Methuer, London, p.225-245.
#
#		This script will create a map of surface area for each pixel
#		using slope and trigonometry. A map of plan area is create as
#		ns_res*ew_res. Using the specified moving window size, maps of
#		the sum of areas are created, and then the ratio is calculated
#		with r.mapcalc.
#
#		If the user does not specify the output map name, it will be
#		set to INPUT_MAP_roughness_NxN
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
#% key: window
#% type: integer
#% description: Window size (3,5,7,...,25)
#% required : no
#% answer : 3
#%end
#%option
#% key: rough
#% gisprompt: old,cell,raster
#% type: string
#% description: Output raster map 
#% required : no
#%end


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

if [ "$GIS_OPT_MAP" = "$GIS_OPT_ROUGH" ]; then
	echo ""
	echo "Input elevation map and output roughness map must have different names"
	exit 1
fi

if [ -z "$GIS_OPT_ROUGH" ]; then
    ROUGHNESS="${map%%@*}_area_ratio_${window}x${window}"
else
    ROUGHNESS="$GIS_OPT_ROUGH"
fi


#######################################################################
# what to do in case of user break:
exitprocedure()
{
 g.message -e 'User break!'
 #delete any TMP files:
 g.remove rast=$TMP1,$TMP2,$TMP3,$TMP4 > /dev/null

}
# shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 15


#######################################################################

########################################################################
# get region resolution
nsres="`g.region -p | grep nsres | sed -e s/.*:\ *//`"
ewres="`g.region -p | grep ewres | sed -e s/.*:\ *//`"

########################################################################


#make temp rasters:

TMP1=surfarea_$$
TMP2=planarea_$$
TMP3=sum_surfarea_$$
TMP4=sum_planarea_$$

r.mapcalc $TMP1 = "$nsres*($nsres/cos($slope))"
r.mapcalc $TMP2 = "$nsres*$ewres"

r.neighbors -a input=$TMP1 output=$TMP3 method=sum size=$window
r.neighbors -a input=$TMP2 output=$TMP4 method=sum size=$window

r.mapcalc $ROUGHNESS = "$TMP3 / $TMP4"

r.colors "$ROUGHNESS" color=rainbow

# record metadata
r.support "$ROUGHNESS" title="Relief roughness of \"$GIS_OPT_MAP\"" history=""
r.support "$ROUGHNESS" history="grid size: $grid"


#cleanup
g.remove rast=$TMP1,$TMP2,$TMP3,$TMP4 > /dev/null


echo ""
if [ -n "$GIS_OPT_ROUGH" ] ; then
    echo "Surface roughness map created and named [$ROUGHNESS]."
else
    echo "Surface roughness map created and named [$ROUGHNESS]. Consider renaming."
fi

echo "Done."
exit 0
