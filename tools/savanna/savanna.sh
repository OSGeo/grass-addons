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

echo 'Setting up parameters...'
. "savanna_global_parameters.sh"
export parameter_file="/home/jongreen/code/grass/savanna/v06/savanna_parameters_00008m_rsun.sh"
. $parameter_file

echo 'Checking gridengine...'
. $gridengine_settings

# Check for all required files.

# Create a unique name based on time used as the prefix.
unique_prefix_suffix=$(date +%s)
export prefix="savanna_"$unique_prefix_suffix

# Some standard naming for temp files.
export tiling_grid_suffix="_tiling_grid"

# Create working directory.   
# Should use mktemp -d
export working_tmp=$savanna_tmp/$prefix
mkdir $working_tmp

### Step 1: Initialize tiling.
echo 'Creating tiling script...'

# export init_prefix=$prefix"_init"
export init_mapset=$prefix"_init"

# echo $working_tmp/areas.txt

echo "qsub -N ${prefix}_init -sync y -o $working_tmp -e $working_tmp \
-v \
savanna_path=$savanna_path,\
savanna_init_job_file=$savanna_init_job_file,\
savanna_init_grass_file=$savanna_init_grass_file,\
tilexsize=$tilexsize,\
tileysize=$tileysize,\
tileoverlap=$tileoverlap,\
grassdata_directory=$grassdata_directory,\
base_location=$base_location,\
init_mapset=$init_mapset,\
tiling_grid=$init_mapset$tiling_grid_suffix,\
gregion=\"$gregion\",\
mask=$mask,\
areas_file=$working_tmp/areas.txt \
$savanna_path/$savanna_init_job_file" | sort > $working_tmp/${prefix}_sge_init.sh

# Submit the initialization script to grid engine.
echo 'Submitting tiling script to gridengine...'
sh $working_tmp/${prefix}_sge_init.sh

### Step 2: Perform tiled processing.
# Read in number of areas.
. $working_tmp/areas.txt
# areas=108
numdigits=$(expr length $areas)

for tile in $(seq 1 $areas)
do
tile_unique_id=$(printf "%0"$numdigits"d\n" $tile)
echo "qsub -N ${prefix}_tiling_$tile_unique_id -o $working_tmp -e $working_tmp \
-hold_jid ${prefix}_init \
-v \
tile=$tile,\
savanna_path=$savanna_path,\
savanna_tiling_job_file=$savanna_tiling_job_file,\
savanna_tiling_grass_file=$savanna_tiling_grass_file,\
tileoverlap=$tileoverlap,\
grassdata_directory=$grassdata_directory,\
base_location=$base_location,\
init_mapset=$init_mapset,\
tile_mapset=$prefix\_$tile_unique_id,\
tiling_grid=$init_mapset$tiling_grid_suffix,\
additional_searchpaths=$additional_searchpaths,\
gregion=\"$gregion\",\
command=\"$command\" \
$savanna_path/$savanna_tiling_job_file"
done > $working_tmp"/"$prefix"_sge_tiling.sh"

sh $working_tmp"/"$prefix"_sge_tiling.sh"

### Step 3: Crop and copy the tiles into a single mapset
# Note: this seems to interrupt itself with concurrent mapset access, so
#  I am going to restrict it based on the previous tile.

# The first tile has no dependency on other tiles, so we allow it to run as usual:

let tile=1
tile_unique_id=$(printf "%0"$numdigits"d\n" $tile)
echo "qsub -N ${prefix}_copy_$tile_unique_id -o $working_tmp -e $working_tmp \
-v \
tile=$tile,\
tile_unique_id=$tile_unique_id,\
prefix=$prefix,\
savanna_path=$savanna_path,\
savanna_copy_job_file=$savanna_copy_job_file,\
savanna_copy_grass_file=$savanna_copy_grass_file,\
grassdata_directory=$grassdata_directory,\
base_location=$base_location,\
init_mapset=$init_mapset,\
tile_mapset=$prefix\_$tile_unique_id,\
tiling_grid=$init_mapset$tiling_grid_suffix,\
outputs=\"${outputs[*]}\",\
gregion=\"$gregion\" \
$savanna_path/$savanna_copy_job_file" > $working_tmp"/"$prefix"_sge_copy.sh"

for tile in $(seq 2 $areas)
do
let tile_prev=$tile-1
tile_unique_id_prev=$(printf "%0"$numdigits"d\n" $tile_prev)
tile_unique_id=$(printf "%0"$numdigits"d\n" $tile)
echo "qsub -N ${prefix}_copy_$tile_unique_id -o $working_tmp -e $working_tmp \
-hold_jid ${prefix}_copy_$tile_unique_id_prev \
-v \
tile=$tile,\
tile_unique_id=$tile_unique_id,\
prefix=$prefix,\
savanna_path=$savanna_path,\
savanna_copy_job_file=$savanna_copy_job_file,\
savanna_copy_grass_file=$savanna_copy_grass_file,\
grassdata_directory=$grassdata_directory,\
base_location=$base_location,\
init_mapset=$init_mapset,\
tile_mapset=$prefix\_$tile_unique_id,\
tiling_grid=$init_mapset$tiling_grid_suffix,\
outputs=\"${outputs[*]}\",\
gregion=\"$gregion\" \
$savanna_path/$savanna_copy_job_file"
done >> $working_tmp"/"$prefix"_sge_copy.sh"

sh $working_tmp"/"$prefix"_sge_copy.sh"


### Step 4: Mosaic all the files together.
# Note: this seems to interrupt itself with concurrent mapset access, so
#  I am going to restrict it based on the previous tile.

echo qsub -N ${prefix}_mosaic -o $working_tmp -e $working_tmp \
-hold_jid ${prefix}_copy_"*" \
-v \
savanna_path=$savanna_path,\
savanna_mosaic_job_file=$savanna_mosaic_job_file,\
savanna_mosaic_grass_file=$savanna_mosaic_grass_file,\
grassdata_directory=$grassdata_directory,\
base_location=$base_location,\
init_mapset=$init_mapset,\
prefix=$prefix,\
tiling_grid=$init_mapset$tiling_grid_suffix,\
gregion=\"$gregion\",\
outputs=\"${outputs[*]}\",\
numdigits=$numdigits,\
areas_file=$working_tmp/areas.txt \
$savanna_path/$savanna_mosaic_job_file | sort > $working_tmp/$prefix\_sge\_mosaic.sh

echo 'Submitting mosaic script to gridengine...'
sh $working_tmp/$prefix\_sge\_mosaic.sh

exit 0
