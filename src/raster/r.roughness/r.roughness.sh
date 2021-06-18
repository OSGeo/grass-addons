#!/bin/sh
#
############################################################################
#
# MODULE:	r.roughness.sh
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
#		This script will create square sub-regions with size defined by
#		the option GRID. In each sub-region, the real and planar areas
#		will be calculated by r.surf.area, and the results (points at 
#		the center of sub-regions) will be interpolated with v.surf.rst.
#		The user also can set the tension and smooth parameters.
#
# COPYRIGHT:	(C) 2006-2009 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
#############################################################################

#%Module
#% description: Calculates surface roughness
#%End
#%option
#% key: map
#% gisprompt: old,cell,raster
#% type: string
#% description: Input raster elevation map
#% required : yes
#%end
#%option
#% key: grid
#% type: integer
#% description: Grid size in meters
#% required : no
#% answer : 1000
#%end
#%option
#% key: rough
#% gisprompt: old,cell,raster
#% type: string
#% description: Output raster map 
#% required : no
#%end
#%option
#% key: tension
#% type: double
#% description: Spline tension parameter
#% required : no
#% answer : 40.
#%end
#%option
#% key: smooth
#% type: double
#% description: Spline smoothing parameter
#% required : no
#% answer : 0.1
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


#### check if we have awk
if [ ! -x "`which awk`" ] ; then
    echo "$PROG: awk required, please install awk or gawk first" 2>&1
    exit 1
fi

# set environment so that awk works properly in all languages
unset LC_ALL
export LC_NUMERIC=C


TMP_ascii="`g.tempfile pid=$$`"
if [ $? -ne 0 ] || [ -z "${TMP_ascii}" ] ; then
    echo "ERROR: unable to create temporary files" 1>&2
    exit 1
fi


#vars

elev=$GIS_OPT_MAP
grid=$GIS_OPT_GRID
#rough=$GIS_OPT_ROUGH

#check if input file exists
eval `g.findfile element=cell file=$elev`
if [ -z "$name" ] ; then
   echo "ERROR: map <$elev> not found."
   exit 1
fi

if [ "$GIS_OPT_MAP" = "$GIS_OPT_ROUGH" ]; then
	echo ""
	echo "Input elevation map and output roughness map must have different names"
	exit 1
fi

if [ -z "$GIS_OPT_ROUGH" ]; then
    ROUGHNESS="${elev}_roughness_${grid}"
else
    ROUGHNESS="$GIS_OPT_ROUGH"
fi


#######################################################################
cleanup() 
{
    eval `g.findfile elem=windows file="tmp_region.$$" | grep '^name='`
    if [ -n "$name" ] ; then
	unset WIND_OVERRIDE
	g.remove region="tmp_region.$$" --quiet
    fi
    rm -f "$TMP_ascii"
    g.remove vect="TMP_vect_$$" --quiet
}

# what to do in case of user break:
exitprocedure()
{
    echo "User break!"
    cleanup
    exit 1
}
# shell check for user break (signal list: trap -l)
trap "exitprocedure" 2 3 15


#######################################################################

########################################################################
# get region limits
maxnorth="`g.region -p | grep north | sed -e s/.*:\ *//`"
maxsouth="`g.region -p | grep south | sed -e s/.*:\ *//`"
maxwest="` g.region -p | grep west | sed -e s/.*:\ *//`"
maxeast="` g.region -p | grep east | sed -e s/.*:\ *//`"

# setup internal region
g.region save="tmp_region.$$"
WIND_OVERRIDE="tmp_region.$$"
export WIND_OVERRIDE

ns_dist="`echo $maxnorth $maxsouth |awk '{printf("%f", $1 - $2);}'`"
ew_dist="`echo $maxeast $maxwest | awk '{printf("%f", $1 - $2);}'`"
rows="`echo $ns_dist $grid | awk '{printf("%.0f", $1 / $2);}'`"
cols="`echo $ew_dist $grid | awk '{printf("%.0f", $1 / $2);}'`"

########################################################################

north=$maxnorth
west=$maxwest
south="`echo $north $grid | awk '{printf("%f", $1 - $2);}'`"
east="`echo $west $grid | awk '{printf("%f", $1 + $2);}'`"

# number of region
no_of_region="0"

### rows N-S
while [ `echo $south $maxsouth |awk '{printf("%d", $1 >= $2);}'` = 1 ];
do 
    echo "north -> south"    # 
    # columns W-E
    while [ `echo $east $maxeast |awk '{printf("%d", $1<= $2);}'` = 1 ];
    do
        echo "west -> east"  # 
       
        g.region n=$north s=$south w=$west e=$east

        dx="`echo $east $west |awk '{printf("%f", $1 - $2);}'`"
        dy="`echo $north $south |awk '{printf("%f", $1 - $2);}'`"
        coord_x="`echo $west $dx |awk '{printf("%f", $1 + $2);}'`"
        coord_y="`echo $north $dy |awk '{printf("%f", $1 - $2);}'`"

        planarea="`r.surf.area input=$elev | grep Current | sed -e s/.*:\ *//`"
        realarea="`r.surf.area input=$elev | grep Estimated | sed -e s/.*:\ *//`"

	echo "$coord_x $coord_y $realarea $planarea" | \
	   awk '{printf "%d %d %f\n", $1, $2, $3 / $4}'>> "$TMP_ascii"

        west=$east
        east="`echo $west $grid |awk '{printf("%f", $1 + $2);}'`"
        
        no_of_region="`echo $no_of_region |awk '{printf("%.0f", $1 + 1);}'`"
        regions_total="`echo $rows $cols |awk '{printf("%.0f", $1 * $2);}'`"
        echo "--------- REGION NUMBER $no_of_region OF $regions_total ----------"

    done
    
    north=$south
    south="`echo $north $grid |awk '{printf("%f", $1 - $2);}'`"
    
    # go west
    west=$maxwest
    east="`echo $west $grid |awk '{printf("%f", $1 + $2);}'`"
done


# back to original region
unset WIND_OVERRIDE
g.remove region="tmp_region.$$" --quiet


v.in.ascii input="$TMP_ascii" output="TMP_vect_$$" format=point \
   fs=space skip=0 x=1 y=2 z=3 cat=0 -z

v.surf.rst input="TMP_vect_$$" layer=0 elev="$ROUGHNESS" zmult=1.0 \
   tension="$GIS_OPT_TENSION" smooth="$GIS_OPT_SMOOTH"

r.colors "$ROUGHNESS" color=rainbow

# record metadata
r.support "$ROUGHNESS" title="Relief roughness of \"$GIS_OPT_MAP\"" history=""
r.support "$ROUGHNESS" history="grid size: $grid"


### cleaning
cleanup

echo ""
if [ -n "$GIS_OPT_ROUGH" ] ; then
    echo "Surface roughness map created and named [$ROUGHNESS]."
else
    echo "Surface roughness map created and named [$ROUGHNESS]. Consider renaming."
fi

echo "Done."
exit 0
