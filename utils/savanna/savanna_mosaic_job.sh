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

export tile_output_name=$output_prefix"_"$day_unique_id
# export temp_mapset=$tile_output_name
# This could set up an infinite loops, so be careful.
# We need to suppress the output -- this loop works fine
# except the output file will grow out of control.
export GRASS_BATCH_JOB=$savanna_path/$savanna_mosaic_grass_file
# for i in (( ; ; )); do
# while true; do
grass64 -c -text $grassdata_directory/$base_location/$init_mapset
#  if [ $? -eq 0 ] ; then
#        exit 1             #Abandon the loop.
#  fi
# sleep 1
# done
# Once its done, remove the temp directories (BE CAREFUL WITH THIS).

# eval rm -rf $grassdata_directory'/'$base_location'/'$tile_output_name'*'
# ls $grassdata_directory'/'$base_location'/'$tile_output_name'*'
# echo $grassdata_directory"/"$base_location"/"$tile_output_name"_*"


