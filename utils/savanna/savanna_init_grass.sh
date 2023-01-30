#!/bin/bash
#$ -S /bin/bash
############################################################################
#
# MODULE:       savanna
# AUTHOR(S):    Jonathan A. Greenberg <savanna@estarcion.net> and Quinn Hart
# PURPOSE:      Distributes R raster commands across a gridengine cluster.
# COPYRIGHT:    (C) 2010 by the Jonathan A. Greenberg
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
##############################################################################!/bin/bash

# savanna GRASS_BATCH_JOB to create the tiling grid.

# Set the gregion
$gregion
eval `$gregion -g`
# g.region -p

if [ $? -ne 0 ] ; then
        echo 'Error in setting g.region...'
        exit 1              #Abandon the loop.
fi

# Calculate the base number of tiles to use.
numxtiles=$(echo "scale=0; (($w - $e)/$ewres)/$tilexsize" | bc)
if ((numxtiles < 0)) ; then
        let "numxtiles = numxtiles * -1"
fi
smallxtilesize=$(echo "scale=0; (($w - $e)/$ewres) % $tilexsize" | bc)
if ((smallxtilesize != 0)); then
        let 'numxtiles++'
fi

numytiles=$(echo "scale=0; (($n - $s)/$nsres)/$tileysize" | bc)
if ((numytiles < 0))
        then let "numytiles = numytiles * -1"
fi
smallytilesize=$(echo "scale=0; (($n - $s)/$nsres) % $tileysize" | bc)
if ((smallytilesize != 0))
        then let 'numytiles++'
fi

eval $gregion
let 'boxx = ewres*tilexsize'
let 'boxy = nsres*tileysize'

v.mkgrid map=$tiling_grid grid=$numytiles,$numxtiles position=coor coor=$w,$s box=$boxy,$boxx angle=0 --overwrite --quiet
if [ $? -ne 0 ] ; then
        echo 'Error in v.mkgrid...'
        exit 1              #Abandon the loop.
fi

# The next step should be optional only if the user provided a mask.
#v.select ainput=$output_prefix$tiling_grid_suffix atype=area alayer=1 binput=$mask btype=point,line,area blayer=1 output=$tiling_vector"_uncor" operator=overlap --overwrite --quiet
#if [ $? -ne 0 ] ; then
#        echo 'Error in v.select...'
#        exit 1              #Abandon the loop.
#fi
#v.category input=$tiling_vector"_uncor" output=$tiling_vector"_stripped" option=del --overwrite --quiet
#if [ $? -ne 0 ] ; then
#        echo 'Error in v.category pass 1...'
#        exit 1              #Abandon the loop.
#fi
#v.category input=$tiling_vector"_stripped" output=$tiling_vector option=add type=centroid layer=1 cat=1 step=1 --overwrite --quiet
#if [ $? -ne 0 ] ; then
#        echo 'Error in v.category pass 2...'
#        exit 1              #Abandon the loop.
#fi

# Need to do some cleaning

eval `v.info -t map=$tiling_grid layer=1 --quiet`
if [ $? -ne 0 ] ; then
        echo 'Error in v.info...'
        exit 1              #Abandon the loop.
fi

echo $areas
echo $areas_file

echo export areas=$areas > $areas_file

exit 0
