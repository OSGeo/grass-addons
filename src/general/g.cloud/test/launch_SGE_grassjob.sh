#!/bin/sh

############################################################################
#
# MODULE:       launch_SGE_grassjob.sh.template
# AUTHOR(S):    Markus Neteler
#               Modify by Luca Delucchi for g.cloud
#
# PURPOSE:      Launch GRASS GIS job on Grid Engine
#
# COPYRIGHT:    (C) 2008-2011 by Markus Neteler
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

## Grid Engine settings
# request Bourne shell as shell for job
#$ -S /bin/sh
#
# run in current working directory
#$ -cwd
#
#$ -l mem_free=1700M
#
####################################

## DEBUG
#set -x

# better say where to find libs and bins:
export PATH=$PATH:/usr/local/bin:$HOME
export LD_LIBRARY_PATH=$MYLD_LIBRARY_PATH
MYGRASS_ADDON_PATH=$HOME/.grass8/addons/scripts/

#### DON'T TOUCH THE VARIABLES BELOW
# generate machine (blade) unique TMP string
UNIQUE=`mktemp`
MYTMP=`basename $UNIQUE`
# use Grid Engine jobid + unique string as MAPSET to avoid GRASS lock
MYMAPSET=sge.$JOB_ID.$MYTMP
MYUSER=$MYMAPSET
# The target mapset where output data will be stored 
TARGETMAPSET=PERMANENT
# the job
GRASS_BATCH_JOB=$GRASSCRIPT

# path to GRASS binaries and libraries:
export GISBASE=`grass --config path`
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$GISBASE/lib

# use process ID (PID) as GRASS lock file number:
export GIS_LOCK=$$
export GRASS_MESSAGE_FORMAT=plain
export TERM=linux

################ nothing to change below ############

# Set the global GRASS settings file to individual file name
mkdir -p $HOME/.grass8/
MYGISRC="$HOME/.grass8/rc.$MYUSER.`uname -n`.$MYTMP"

#generate GISRCRC
echo "GRASS_ADDON_PATH: $MYGRASS_ADDON_PATH" > "$MYGISRC"
echo "GISDBASE: $GRASSDBASE" >> "$MYGISRC"
echo "LOCATION_NAME: $MYLOC" >> "$MYGISRC"
echo "MAPSET: $MYMAPSET" >> "$MYGISRC"
echo "GRASS_GUI: text" >> "$MYGISRC"

# path to GRASS settings file
export GISRC=$MYGISRC

mkdir $GRASSDBASE/$MYLOC/$MYMAPSET
# fix WIND in the newly created mapset
cp "$GRASSDBASE/$MYLOC/PERMANENT/DEFAULT_WIND" "$GRASSDBASE/$MYLOC/$MYMAPSET/WIND"
db.connect -c --quiet

# run the GRASS job:
. $GRASS_BATCH_JOB

# cleaning up temporary files
$GISBASE/etc/clean_temp > /dev/null
rm -f ${MYGISRC}
rm -rf $HOME/tmp/grass8-$USER-$GIS_LOCK

# leave breadcrumb to find related mapsets back when moving results
# into final mapset:
echo "touch $GRASSDBASE/$MYLOC/$MYMAPSET/$MYPID" 1>&2

touch $GRASSDBASE/$MYLOC/$MYMAPSET/$MYPID

echo "Hopefully successfully finished at `date` *************"

exit 0
