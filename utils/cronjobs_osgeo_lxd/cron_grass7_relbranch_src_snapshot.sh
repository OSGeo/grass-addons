#!/bin/sh

# script to build GRASS sources package from git relbranch of 7.X
# (c) GPL 2+ Markus Neteler <neteler@osgeo.org>
# Markus Neteler 2002, 2003, 2005, 2006, 2007, 2008, 2012, 2014, 2015, 2016, 2017, 2018, 2019, 2020
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
## prep, neteler@osgeo6:$
# mkdir -p ~/src
# cd ~/src
# for i in 2 4 6 ; do git clone ​https://github.com/OSGeo/grass.git releasebranch_7_$i ; done
# for i in 2 4 6 ; do (cd releasebranch_7_$i ;  git checkout releasebranch_7_$i ) ; done
#
###################################################################

MAINDIR=/home/neteler

BRANCH=`curl https://api.github.com/repos/osgeo/grass/branches | grep releasebranch_7 | grep '"name":' | cut -f4 -d'"' | sort -V | tail -n 1`

GMAJOR=`echo $BRANCH | cut -f2 -d"_"`
GMINOR=`echo $BRANCH | cut -f3 -d"_"`

GVERSION=$GMAJOR.$GMINOR.git
DOTVERSION=$GMAJOR.$GMINOR
GSHORTGVERSION=$GMAJOR$GMINOR

###################
# where to find the GRASS sources (git clone):
SOURCE=$MAINDIR/src/

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

# be sure to be on branch
git checkout $BRANCH

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
