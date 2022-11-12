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
#$ -S /bin/bash
# This is a single r.sun job for use with grid engine.  The inputs are:
#       grassdata_directory = base grass data directory
#       base_location = grass location
#       base_mapset = grass mapset
#       output_prefix
#       output_suffix
#       dem =
#       tiling_vector = vector containing rectangular polygons defining each tile
#       overlapsize = buffering size in pixels to use for each tile
#       tile = tile ID
# TODO: This can probably be parallelized, if we put a wait condition for any other similarly named jobs.

outputs=($outputs)

$gregion
if [ $? -ne 0 ] ; then
        echo 'Error in g.region pass 1...'
        exit 1              #Abandon the loop.
fi

outputs_N=${#outputs[*]}
# We use the first tile to define what the outputs are.
tile_unique_id=$(printf "%0"$numdigits"d\n" 1)
unset MAPS
for output_loop in $(seq 1 $outputs_N)
do
echo $output_loop
echo "base_MAPS=(g.mlist type=rast sep=space mapset=${prefix}_$tile_unique_id pat=${outputs[($output_loop-1)]})"
base_MAPS=(`g.mlist type=rast sep=space mapset=${prefix}_$tile_unique_id pat=${outputs[($output_loop-1)]}`)
base_MAPS_N=${#base_MAPS[*]}
echo $base_MAPS
for maps_loop in $(seq 1 $base_MAPS_N)
do
echo $maps_loop
echo "MAPS=(`g.mlist type=rast sep=, pat=${base_MAPS[($maps_loop-1)]}_tile_*`)"
MAPS=(`g.mlist type=rast sep=, pat=${base_MAPS[($maps_loop-1)]}_tile_*`)
echo $MAPS
g.region rast=${MAPS[*]}
if [ $? -ne 0 ] ; then
        echo 'Error in g.region pass 5 for beam...'
        exit 1              #Abandon the loop.
fi
r.patch in=$MAPS out=${base_MAPS[($maps_loop-1)]}
#if [ $? -ne 0 ] ; then
#        echo 'Error in r.patch...'
#        exit 1              #Abandon the loop.
#fi
unset MAPS
done
unset base_MAPS
done

# Now clean up the files
# g.mremove -f rast=$tile_output_name"_*_beam",$tile_output_name"_*_diff"
# echo $grassdata_directory/$base_location/$tile_output_name"_*"
# rm -rf $grassdata_directory/$base_location/$tile_output_name"_*"

exit 0
