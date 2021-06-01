#!/bin/bash

###############################################################################
#
# MODULE: boxcount.sh
#
# AUTHORS:
#
# Original author:
# Mark Lake  1/9/99
# University College London
# Institute of Archaeology
# 31-34 Gordon Square
# London.  WC1H 0PY
# email: mark.lake@ucl.ac.uk
# 
#  Adaptations for grass63:
#  Florian Kindl, 2006-10-02
#  University of Innsbruck
#  Institute of Geography
#  email: florian.kindl@uibk.ac.at
#
# PURPOSE: Study  how the boxcounting fractal dimension varies across a raster map.
# COPYRIGHT: (C) 2008 by the authors.
#        This program is free software under the GNU General Public
#        License (>=v2). Read the file COPYING that comes with GRASS
#        for details.
###############################################################################


#%Module
#%  description: Study  how the boxcounting fractal dimension varies across a raster map.
#%  keywords: raster, fractality
#%End
#
#%option
#% key: input
#% type: string
#% gisprompt: in,cell,raster
#% description: map to be analysed
#% required : yes
#%end
#
#%option
#% key: output
#% type: string
#% gisprompt: new,cell,raster
#% description: name for fractal dimension map
#% required : yes
#%end
#
#% option
#% key: boxsize
#% type: integer
#% description: size of moving window (16,32,64,128,256,512... are best)
#% required : yes
#% end
#
#% option
#% key: gridsize
#% type: integer
#% description: distance between centre of each window
#% required : yes
#% end
#
#% option
#% key: k
#% type: integer
#% description: Max 1/box size is 2^k
#% required : yes
#% end
#
#% option
#% key: saturation
#% type: double
#% description: Occupied boxes as fraction of data points at saturation
#% required : yes
#% end
#
#% option
#% key: resolution
#% type: integer
#% description: Smallest 1/box size to use in regression (= 1, 2, 4,...)
#% required : yes
#% end


# Check whether running GRASS

if [ -z $GISRC ]
    then
	echo "Sorry, you are not running GRASS " 1>&2
	exit 1
fi

# parsing arguments

if   [ "$1" != "@ARGS_PARSED@" ]
then
    exec g.parser "$0" "$@"
fi


# check if we have awk
   if [ ! -x "`which awk`" ] ; then
   	echo "ERROR: awk required, please install awk or gawk first" 1>&2
   	exit 1
   fi

# Read GRASS environment variables
eval `g.gisenv`


# Read current region into n, s, e, w
eval `g.region -g`

# is equivalent to this:
#n=`g.region -p | awk ' /north:/ { print $2 }'`
#s=`g.region -p | awk ' /south:/ { print $2 }'`
#e=`g.region -p | awk ' /east:/  { print $2 }'`
#w=`g.region -p | awk ' /west:/  { print $2 }'`


# Save map to be analysed
binarymap=$GIS_OPT_INPUT

# Get output file name
record=$GIS_OPT_OUTPUT

# Get parameters for r.boxcount
k=$GIS_OPT_K
saturation=$GIS_OPT_SATURATION
resolution=$GIS_OPT_RESOLUTION

#echo "$GIS_OPT_SATURATION"
#echo "$k $saturation $resolution"


# create tempfiles
tempfile="`g.tempfile $$`_${record}_fract"
ascirast="`g.tempfile $$`_${record}_fract_rast"
#tempfile="/tmp/fract"
#ascirast="/tmp/fract_rast"

# Get boxsize (i.e. region size for r.boxcount)
boxsize=$GIS_OPT_BOXSIZE

twiceboxsize=`expr $boxsize + $boxsize`
halfboxsize=`expr $boxsize / 2`

# Get gridsize (i.e. distance between centre of each region
# used for boxcounting).  Can be greater or less than boxsize.
gridsize=$GIS_OPT_GRIDSIZE

halfgridsize=`expr $gridsize / 2`

# Calculate appropriate region to eliminate edge effect

if [ $boxsize -ge $gridsize ]
then
    startnorth=`expr $n - $halfboxsize`
    stopnorth=`expr $s + $halfboxsize + $gridsize`
    startwest=`expr $w + $halfboxsize`
    stopwest=`expr $e - $halfboxsize - $gridsize`
else
    startnorth=`expr $n - $halfgridsize`
    stopnorth=`expr $s + $halfgridsize + $gridsize`
    startwest=`expr $w + $halfgridsize`
    stopwest=`expr $e - $halfgridsize - $gridsize`
fi

# Loop over grid

newgridnorth=$startnorth
row=0
countnorth=0
while [ $newgridnorth -ge $stopnorth ]
do
    row=`expr $row + 1`
    newgridnorth=`expr $startnorth - $countnorth`
    countnorth=`expr $countnorth + $gridsize`  

    col=0
    countwest=0
    newgridwest=$startwest
    while [ $newgridwest -le $stopwest ]
    do
	
	col=`expr $col + 1`
    echo -ne "\r" 1>&2
	echo -n "row = $row  col = $col   " 1>&2
	newgridwest=`expr $startwest + $countwest`
	countwest=`expr $countwest + $gridsize`
				 
# Calculate box for this point on the grid

	newnorth=`expr $newgridnorth + $halfboxsize`
	newsouth=`expr $newgridnorth - $halfboxsize`
	neweast=`expr $newgridwest + $halfboxsize`
	newwest=`expr $newgridwest - $halfboxsize`

#    eval `g.region n=$newnorth s=$newsouth e=$neweast w=$newwest`
    g.region n=$newnorth s=$newsouth e=$neweast w=$newwest

#    eval `r.boxcount input=$1 k=9 res=4 sat=1 -t  >> /tmp/fract_tmp`
	#echo " "
	echo "row $row col $col" >> $tempfile
    r.boxcount -t input=$binarymap k=$k res=$resolution sat=$saturation  >> $tempfile

    done
done

# Provide info. about appropriate header for use with r.in.ascii

#Header for r.in.ascii"
mapnorth=`expr $startnorth + $halfgridsize`
echo "north:  $mapnorth" > ${ascirast}
mapsouth=`expr $newgridnorth - $halfgridsize`
echo "south:  $mapsouth" >>${ascirast}
mapeast=`expr $newgridwest + $halfgridsize`
echo "east:   $mapeast"  >>${ascirast}
mapwest=`expr $startwest - $halfgridsize`
echo "west:   $mapwest"  >>${ascirast}
echo "rows:   $row"      >>${ascirast}
echo "cols:   $col"      >>${ascirast}


# cat the result into header file
awk '/D/ { print $12}' $tempfile  >> ${ascirast}

# check if we got data:
lines=0
lines=`cat $tempfile|wc -l`
echo $lines 1>&2

if [ $lines -le 0 ]
then
   echo "WARNING: Window too small - could not calculate D!" 1>&2
   echo "Please choose a bigger moving window. Stopped." 1>&2
   rm -f $tempfile ${ascirast}
   exit
else
  # success:
  echo "Importing results..." 1>&2
  #import it into GRASS421:
  #r.in.ascii in=${ascirast} out=$record mult=100

  #import it into GRASS 6:
  r.in.ascii in=${ascirast} out=$record nv=-1

  #remove the tmp.files
  #rm -f $tempfile ${ascirast}
  
  echo "The resulting map showing the fractal dimension is called $record" 1>&2
  echo "Finished." 1>&2
fi

# Reset region
g.region n=$n s=$s e=$e w=$w

exit 0
