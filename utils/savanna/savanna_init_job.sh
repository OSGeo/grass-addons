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

# Note: this sets up an infinite execution loop -- we should probably give
#  10 tries or something and bail.

export GRASS_BATCH_JOB=$savanna_path/$savanna_init_grass_file
echo $GRASS_BATCH_JOB
# while true; do
grass64 -c -text $grassdata_directory/$base_location/$init_mapset
#  if [ $? -eq 0 ] ; then
#        exit 1              #Abandon the loop.
#  fi
# sleep 1
# done
