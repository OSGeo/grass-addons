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
#############################################################################
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

g.region -d
$gregion
g.region -p
if [ $? -ne 0 ] ; then
        echo 'Error in g.region pass 1...'
        exit 1              #Abandon the loop.
fi

# tile_unique_id=$(printf "%0"$numdigits"d\n" $tile)

g.region -g vect=${tiling_grid}_sub_temp@${prefix}_$tile_unique_id
if [ $? -ne 0 ] ; then
        echo 'Error in g.region pass 2 for tile '$tile'...'
        exit 1              #Abandon the loop.
fi
g.region -p
eval `g.region -g`
# I don't know why, but the eastern edge is one half off, so we must correct it.
# corr_e=$(echo "scale=0; ($e-($ewres*0.5))" | bc)

# g.region -a vect=${tiling_grid}_sub_temp@${prefix}_$tile_unique_id e=$corr_e
# g.region -p
# if [ $? -ne 0 ] ; then
#        echo 'Error in g.region pass 4 for tile '$tile'...'
#        exit 1              #Abandon the loop.
# fi

# We loop through each of the outputs
outputs_N=${#outputs[*]}
# echo $outputs_N
unset MAPS
for output_loop in $(seq 1 $outputs_N)
do
# echo $output_loop
# echo "g.mlist type=rast sep=space mapset=${prefix}_$tile_unique_id pat=${outputs[($output_loop-1)]}"
# echo "MAPS=(`g.mlist type=rast sep=space mapset=${prefix}_$tile_unique_id pat=${outputs[($output_loop-1)]}`)"
MAPS=(`g.mlist type=rast sep=space mapset=${prefix}_$tile_unique_id pat=${outputs[($output_loop-1)]}`)
MAPS_N=${#MAPS[*]}
for maps_loop in $(seq 1 $MAPS_N)
do
echo $maps_loop
g.region -p
r.mapcalc ${MAPS[($maps_loop-1)]}_tile_$tile_unique_id=${MAPS[($maps_loop-1)]}@${prefix}_$tile_unique_id
if [ $? -ne 0 ] ; then
        echo 'Error in r.mapcalc for '$tile'...'
        exit 1              #Abandon the loop.
fi
done
unset MAPS
done

exit 0
