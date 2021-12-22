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

# savanna GRASS_BATCH_JOB to process a single tile.

# Set the gregion
$gregion
        if [ $? -ne 0 ] ; then
                echo 'Error in setting g.region...'
                exit 1              #Abandon the loop.
        fi

eval `$gregion -g`

# Add additional search paths, if neccessary.
g.mapsets addmapset=$additional_searchpaths 'fs= ,' 

g.region -p
# echo $tiling_grid"@"$init_mapset

	let "buffersize=ewres*tileoverlap"

        v.extract input=$tiling_grid"@"$init_mapset \
                 output=$tiling_grid"_sub_temp" type=area layer=1 new=-1 list=$tile --overwrite
        if [ $? -ne 0 ] ; then
                echo 'Error in v.extract...'
                exit 1              #Abandon the loop.
        fi
        v.buffer input=$tiling_grid"_sub_temp" \
                output=$tiling_grid"_sub_temp_buffer" \
                type=area layer=1 buffer=$buffersize scale=1.0 tolerance=0.01 --overwrite --quiet
        if [ $? -ne 0 ] ; then
                echo 'Error in v.buffer...'
                exit 1              #Abandon the loop.
        fi
        g.region -a vect=$tiling_grid"_sub_temp_buffer" --quiet
	g.region -p
        if [ $? -ne 0 ] ; then
                echo 'Error in setting g.region...'
                exit 1              #Abandon the loop.
        fi
echo $command
$command
        if [ $? -ne 0 ] ; then
                echo 'Error in command...'
                exit 1              #Abandon the loop.
        fi

exit 0
