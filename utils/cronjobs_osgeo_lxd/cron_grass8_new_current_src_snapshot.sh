#!/bin/sh

# script to build GRASS 8 new_current (8.3) sources package from the main branch
# (c) GPL 2+ Markus Neteler <neteler@osgeo.org>
# Markus Neteler 2002, 2003, 2005, 2006, 2007, 2008, 2012, 2015, 2018-2022
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
## prep
# git clone https://github.com/OSGeo/grass.git main
#
###################################################################

MAINDIR=/home/neteler
GMAJOR=8
GMINOR=3
GVERSION=$GMAJOR.$GMINOR.git
DOTVERSION=$GMAJOR.$GMINOR
GSHORTGVERSION=$GMAJOR$GMINOR

###################
# where to find the GRASS sources (git clone):
SOURCE=$MAINDIR/src/
BRANCH=main
# where to put the resulting .tar.gz file:
TARGETMAIN=/var/www/code_and_data/
TARGETDIR=$TARGETMAIN/grass${GSHORTGVERSION}/source/snapshot
PACKAGENAME=grass-${GVERSION}_

############################## nothing to change below:

MYMAKE="nice make"
TAR=tar

# catch CTRL-C and other breaks:
trap "echo 'user break.' ; exit" 2 3 9 15

halt_on_error()
{
  echo "ERROR: $1"
  exit 1
}

# create a source code snapshot:
CWD=`pwd`

mkdir -p $TARGETDIR
cd $SOURCE/$BRANCH/
date

#clean up
$MYMAKE distclean > /dev/null 2>&1

# cleanup leftover garbage
git status | grep '.rst' | xargs rm -f
rm -rf lib/python/docs/_build/ lib/python/docs/_templates/layout.html
rm -f config_${DOTVERSION}.git_log.txt ChangeLog

# reset i18N POT files to git, just to be sure
git checkout locale/templates/*.pot

## hard reset local git repo (just in case)
#git checkout main && git reset --hard HEAD~1 && git reset --hard origin

echo "git update..."
git fetch --all --prune       || halt_on_error "git fetch error!"
# we dont have upstream in this cronjob repo
git merge origin/$BRANCH

git status

#generate changelog
touch include/Make/Platform.make # workaround for https://trac.osgeo.org/grass/ticket/3853
make changelog
rm -f include/Make/Platform.make

# go to parent for packaging
cd ..

date
#package it (we rename the directory to have the date inside the package):
DATE=`date '+_%Y_%m_%d'`
mv $BRANCH $PACKAGENAME\src_snapshot$DATE
# exclude version control system directories (the flag order matters!)
$TAR cfz $PACKAGENAME\src_snapshot$DATE.tar.gz --exclude-vcs $PACKAGENAME\src_snapshot$DATE
mv $PACKAGENAME\src_snapshot$DATE $BRANCH

#remove old snapshot:
rm -f $TARGETDIR/$PACKAGENAME\src_snapshot*
rm -f $TARGETDIR/ChangeLog.gz

#publish the new one:
cd $BRANCH/
cp -p ChangeLog AUTHORS CHANGES CITING COPYING GPL.TXT INSTALL REQUIREMENTS.html $TARGETDIR

cd ..
gzip $TARGETDIR/ChangeLog
cp $PACKAGENAME\src_snapshot$DATE.tar.gz $TARGETDIR
rm -f $PACKAGENAME\src_snapshot$DATE.tar.gz
chmod a+r,g+w $TARGETDIR/* 2> /dev/null
chgrp grass $TARGETDIR/*   2> /dev/null

# link for convenience:
(cd $TARGETDIR ; rm -f $PACKAGENAME\src_snapshot_latest.tar.gz ; ln -s $PACKAGENAME\src_snapshot$DATE.tar.gz $PACKAGENAME\src_snapshot_latest.tar.gz)

echo "Written to: $TARGETDIR
https://grass.osgeo.org/grass${GSHORTGVERSION}/source/snapshot/"

exit 0
