#!/bin/sh
#
############################################################################
#
# MODULE:	r.strahler.sh
# AUTHOR(S):	Annalisa Minelli, Ivan Marchesini
# PURPOSE:	Create a vector map of strahler ordered streems of a single 
#           basin, starting from a DEM.   
#           The script extracts from a DEM the network (by using 
#           r.watershed), converts the network to vector lines, 
#           cleans the topology, lets you decide an outlet for your basin, 
#           and executes v.strahler for the upstream basin.
#
# COPYRIGHT:	(C) 2008 by the GRASS Development Team
#
#		This program is free software under the GNU General Public
#		License (>=v2). Read the file COPYING that comes with GRASS
#		for details.
#
# TODO: solve stability problems for low area threshold 
#############################################################################
#%Module
#%  description: Create a vector map of strahler ordered streems of a single basin starting from a DEM
#%  keywords: strahler, streems, vector
#%End
#%option
#% key: dem
#% type: string
#% key_desc: dem
#% gisprompt: old,cell,raster
#% description: Name of DEM raster map
#% required : yes
#%END
#%option
#% key: thr
#% type: integer
#% description: minimum size of exterior watershed basin
#% required : yes
#%end
#%option
#% key: output
#% type: string
#% gisprompt: new,vector,vector
#% description: Name of streems ordered map created
#% required : yes
#%end
#%option
#% key: textoutput
#% type: string
#% gisprompt: new_file,file,output
#% key_desc: name
#% description: Name for output text file
#% required: yes
#%end
#%option
#% key: bkgrmap
#% type: string
#% key_desc: bkgrmap
#% gisprompt: old,cell,raster
#% description: Name of background map to plot
#% required : no
#%END

if  [ -z "$GISBASE" ] ; then
    echo "You must be in GRASS GIS to run this program." >&2
    exit 1
fi

if [ "$1" != "@ARGS_PARSED@" ] ; then
    exec g.parser "$0" "$@"
fi

dem=$GIS_OPT_DEM
thr=$GIS_OPT_THR
output=$GIS_OPT_OUTPUT
textoutput=$GIS_OPT_TEXTOUTPUT
bkgrmap=$GIS_OPT_BKGRMAP

#check presence of raster MASK, put it aside
MASKFOUND=0
eval `g.findfile element=cell file=MASK`
if [ "$file" ] ; then
   g.message "Raster MASK found, temporarily disabled"
   g.rename MASK,"${TMPNAME}_origmask" --quiet
   MASKFOUND=1
fi

eval `g.gisenv`
: ${GISBASE?} ${GISDBASE?} ${LOCATION_NAME?} ${MAPSET?}
LOCATION=$GISDBASE/$LOCATION_NAME/$MAPSET

#uncomment this line if you need to remove some maps remaining from previous runs
#g.remove rast=rnetwork,rnetwork_thin,rnetwork_b,rnetwork_l,rnetwork_patch,rnetwork_thin2,drainage,MASK,basin vect=vnetwork,vnetwork_b,vnetwork_b_add,vnetwork2,vnetwork_dangle

#get resolution of DEM
res=`g.region -p | grep nsres | cut -f2 -d':' | tr -d ' '`

#find raster streems and plot them
r.watershed elevation=$dem threshold=$thr stream=rnetwork drainage=drainage --overwrite
r.null map=rnetwork setnull=0
r.thin input=rnetwork output=rnetwork_th iterations=200 --overwrite
r.mapcalc "rnetwork_thin=rnetwork_th/rnetwork_th"
d.erase
d.rast map=$bkgrmap
d.rast -o map=rnetwork_thin

#ask the user for zooming and choosing the outlet cell
#-------
echo "


Now, please zoom to the area where you want to put the outlet cross section


"

d.zoom

echo "


Now, please click on the cell representing the cross section


"

#prevent from choosing a wrong cell outside from the streems
cat=2
while [ "$cat" != "1" ]
do
result=`d.what.rast -t -1 rnetwork_thin`
coor=`echo $result | cut -f1 -d ' '`
x=`echo $coor | cut -f1 -d':'`
y=`echo $coor | cut -f2 -d':'`
cat=`echo $result | cut -f3 -d ' ' | tr -d :`
done

#come back to the previous zoom
d.zoom -r

#find the basin and set the mask
r.water.outlet drainage=drainage basin=basin easting=$x northing=$y
d.rast basin
r.null map=basin setnull=0
r.mapcalc "MASK=basin" 
d.rast MASK

#clean raster map and convert it to vector
g.region rast=MASK
r.to.vect input=rnetwork_thin output=vnetwork feature=line --overwrite
d.vect map=vnetwork
v.type input=vnetwork output=vnetwork_b type=line,boundary --overwrite
v.centroids input=vnetwork_b output=vnetwork_b_add option=add layer=1 cat=1 step=1 --overwrite
newres=`echo "$res/4" | bc -l`
g.region res=$newres
v.to.rast input=vnetwork_b_add output=rnetwork_b use=val type=area layer=1 value=1 rows=4096 --overwrite
v.to.rast input=vnetwork output=rnetwork_l use=val type=line layer=1 value=1 rows=4096 --overwrite
r.patch input=rnetwork_b,rnetwork_l output=rnetwork_patch --overwrite
r.thin input=rnetwork_patch output=rnetwork_thin2 iterations=200 --overwrite
r.to.vect input=rnetwork_thin2 output=vnetwork2 feature=line --overwrite

#remove dangles and create polylines
soglia=`echo "sqrt(2*($res^2))+1" | bc -l`
v.clean input=vnetwork2 output=vnetwork_dangle type=line tool=rmdangle thresh=$soglia  --overwrite
v.build.polylines input=vnetwork_dangle output=vnetwork_poly cats=first --overwrite
d.vect vnetwork_poly

#enlarge region to ensure v.strahler get raster values at streems ends and use v.strahler
g.region -a res=$res n=n+$soglia s=s-$soglia e=e+$soglia w=w-$soglia
v.strahler input=vnetwork_poly output=$output dem=$dem sloppy=0 layer=1 txout=$textoutput

#remove temporary files
g.remove rast=rnetwork,rnetwork_thin,rnetwork_b,rnetwork_l,rnetwork_patch,rnetwork_thin2,drainage,MASK,basin vect=vnetwork,vnetwork_b,vnetwork_b_add,vnetwork2,vnetwork_dangle

