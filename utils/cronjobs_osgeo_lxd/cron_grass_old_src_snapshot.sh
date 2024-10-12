#!/bin/sh

# script to build GRASS GIS old current source package from the release branch
# (c) 2002-2024, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
###################################################################
# how it works:
# - it updates locally the GRASS source code from github server
# - packages the source code tarball
#
# Preparations, on server (neteler@grasslxd:$):
#   mkdir -p ~/src
#   cd ~/src
#   git clone https://github.com/OSGeo/grass.git release_branch_8_3
#
###################################################################
# variables for packaging environment (grass.osgeo.org specific)
MAINDIR=/home/neteler
PATH=$MAINDIR/bin:/bin:/usr/bin:/usr/local/bin

# https://github.com/OSGeo/grass/tags
GMAJOR=8
GMINOR=3
GVERSION=$GMAJOR.$GMINOR.git
DOTVERSION=$GMAJOR.$GMINOR
GSHORTGVERSION=$GMAJOR$GMINOR

# fail early
set -e

###################
# where to find the GRASS sources (git clone):
SOURCE=$MAINDIR/src/
BRANCH=releasebranch_${GMAJOR}_${GMINOR}
# where to put the resulting .tar.gz file:
TARGETMAIN=/var/www/code_and_data/
TARGETDIR=$TARGETMAIN/grass${GSHORTGVERSION}/source/snapshot
PACKAGENAME=grass-${GVERSION}_

############################## nothing to change below:

MYMAKE="nice make -j2"
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

# clean up from previous run
touch include/Make/Platform.make
$MYMAKE distclean > /dev/null 2>&1
rm -f grass-$GMAJOR.*-install.sh grass-$GMAJOR.*.tar.gz grass-$GMAJOR.*_bin.txt

# cleanup leftover garbage
git status | grep '.rst' | xargs rm -f
rm -rf lib/python/docs/_build/ lib/python/docs/_templates/layout.html
rm -f config_*.git_log.txt ChangeLog

# reset i18N POT files to git, just to be sure
git checkout locale/templates/*.pot

## hard reset local git repo (just in case)
#git checkout main && git reset --hard HEAD~1 && git reset --hard origin

echo "git update..."
git fetch --all --prune       || halt_on_error "git fetch error!"
# we dont have upstream in this cronjob repo
git merge origin/$BRANCH

git status

# generate changelog
touch include/Make/Platform.make # workaround for https://trac.osgeo.org/grass/ticket/3853
make changelog
rm -f include/Make/Platform.make

# go to parent directory for packaging
cd ..

date
# package it (we rename the directory to have the date inside the package):
DATE=`date '+_%Y_%m_%d'`
mv $BRANCH $PACKAGENAME\src_snapshot$DATE
# exclude version control system directories (the flag order matters!)
$TAR cfz $PACKAGENAME\src_snapshot$DATE.tar.gz --exclude-vcs $PACKAGENAME\src_snapshot$DATE
mv $PACKAGENAME\src_snapshot$DATE $BRANCH

# remove old snapshot:
rm -f $TARGETDIR/$PACKAGENAME\src_snapshot*
rm -f $TARGETDIR/ChangeLog.gz

# publish the new one:
cd $BRANCH/
cp -p ChangeLog AUTHORS CITING CITATION.cff COPYING GPL.TXT INSTALL.md REQUIREMENTS.md $TARGETDIR

cd ..
gzip $TARGETDIR/ChangeLog
cp $PACKAGENAME\src_snapshot$DATE.tar.gz $TARGETDIR
rm -f $PACKAGENAME\src_snapshot$DATE.tar.gz
chmod a+r,g+w $TARGETDIR/* 2> /dev/null
# chgrp grass $TARGETDIR/*   2> /dev/null

# "latest" link for convenience:
(cd $TARGETDIR ; rm -f $PACKAGENAME\src_snapshot_latest.tar.gz ; ln -s $PACKAGENAME\src_snapshot$DATE.tar.gz $PACKAGENAME\src_snapshot_latest.tar.gz)

echo "Written to: $TARGETDIR
https://grass.osgeo.org/grass${GSHORTGVERSION}/source/snapshot/"

exit 0
