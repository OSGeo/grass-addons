#!/bin/sh

############################################################################
#
# MODULE:       cloud_collect.sh
# AUTHOR(S):    Markus Neteler
#               Modify by Luca Delucchi for g.cloud
#
# PURPOSE:      Copy all maps from the temporaneous Grid Engine mapsets into target mapset
#
# COPYRIGHT:    (C) 2011 by Markus Neteler
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

## Grid Engine settings
# request Bourne shell as shell for job
#$ -S /bin/sh

# run in current working directory
#$ -cwd

## DEBUG
#set -x
#echo "Using blade: `uname -n`" 1>&2

if [ $# -ne 5 ] ; then
   echo "Script to move Grid Engine job results to GRASS target mapset"
   echo ""
   echo "Usage: $0 targetgrassdbase targetlocation mail_address remove_file"
   echo ""
   echo "targetgrassdbase = GRASSDBASE where to write files"
   echo "targetlocation = LOCATION where to write files"
   echo "mail_address = Mail address where to send email when jobs finish, put NOOO for no email"
   echo "remove_file = Remove temporary files, put NOOO for no removal"
   echo "" 
   echo "Example:"
   echo "   $0 /path/to/grassdata patUTM32  launch_SGE_grassjob_rsun_energy.sh"
   exit 0
fi

#### start of GRASS 8 setup
# better say where to find libs and bins:
export PATH=$PATH:/usr/local/bin:$HOME
export LD_LIBRARY_PATH=$MYLD_LIBRARY_PATH
MYGRASS_ADDON_PATH=$HOME/.grass8/addons/scripts/

# define location to work in
GRASSDBROOT=$1
MYLOC=$2
MAILADDR=$3
REMOVE=$4
CLOUDID=$5

MYMAPSET="PERMANENT"

# path to GRASS binaries and libraries:
export GISBASE=`grass --config path`
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib64:$GISBASE/lib

# use process ID (PID) as GRASS lock file number:
export GIS_LOCK=$$
export GRASS_MESSAGE_FORMAT=plain
export TERM=linux

# path to GRASS settings file
mkdir -p $HOME/.grass8/
MYGISRC="$HOME/.grass8/rc.gcollectorjob.$MYPID"

#generate GISRCRC
#echo "GRASS_ADDON_PATH: $MYGRASS_ADDON_PATH" > "$MYGISRC"
echo "GISDBASE: $GRASSDBROOT" >> "$MYGISRC"
echo "LOCATION_NAME: $MYLOC" >> "$MYGISRC"
echo "MAPSET: $MYMAPSET" >> "$MYGISRC"
echo "GRASS_GUI: text" >> "$MYGISRC"

# path to GRASS settings file
export GISRC=$MYGISRC

#### end of GRASS 8 setup

echo $MYPID 1>&2


TOCOLLECTFILE=to_be_collected_$MYPID.csv

ls -1 "$GRASSDBROOT/$MYLOC/sge*/${MYPID}" > "$GRASSDBROOT/$MYLOC/$TOCOLLECTFILE"

rm -f "$GRASSDBROOT/$MYLOC/clean_$TOCOLLECTFILE"
for myname in `cat $GRASSDBROOT/$MYLOC/$TOCOLLECTFILE` ; do
    basename `dirname $myname` >> "$GRASSDBROOT/$MYLOC/clean_$TOCOLLECTFILE"
done

LIST=`cat $GRASSDBROOT/$MYLOC/clean_$TOCOLLECTFILE`

echo $LIST 1>&2


for mapset in $LIST ; do
    MAPS=`g.list raster mapset=$mapset`
    for map in $MAPS ; do
        g.copy raster=$map@$mapset,$map --o
    done
done

for mapset in $LIST ; do
    MAPS=`g.list raster3d mapset=$mapset`
    for map in $MAPS ; do
        g.copy raster=$map@$mapset,$map --o
    done
done

for mapset in $LIST ; do
    MAPS=`g.list vector mapset=$mapset`
    for map in $MAPS ; do
        g.copy vector=$map@$mapset,$map --o
    done
done

if [ "$REMOVE" != "NOOO" ] ; then
    rm -f "$GRASSDBROOT/$MYLOC/$MYMAPSET/.gislock"
    rm -f "$GRASSDBROOT/$MYLOC/clean_$TOCOLLECTFILE"
    rm -f "$GRASSDBROOT/$MYLOC/$TOCOLLECTFILE"

    if [ ! -z "$GRASSDBROOT" ] ; then
        if [ ! -z "$MYLOC" ] ; then
            rm -fr "$GRASSDBROOT/$MYLOC/sge*"
        fi
    fi
fi

if [ "$MAILADDR" != "NOOO" ] ; then
    #sh -x cloud_mail.sh $MAILADDR
    sh cloud_mail.sh $MAILADDR
fi

rm -f $MYGISRC

touch cloud_finish_${CLOUDID}

exit 0

