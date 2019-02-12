#!/bin/sh

SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
SCRIPTPATH=`dirname $SCRIPT`

# core repo
DIR=grass-fetch
mkdir $DIR ; cd $DIR
git svn init --stdlayout https://svn.osgeo.org/grass/grass
git svn --authors-file=${SCRIPTPATH}/AUTHORS.txt fetch

# addons repo
DIR=grass-addons-fetch
mkdir $DIR ; cd $DIR
git svn init https://svn.osgeo.org/grass/grass-addons
git svn --authors-file=${SCRIPTPATH}/AUTHORS.txt fetch

# promo
DIR=grass-promo-fetch
mkdir $DIR ; cd $DIR
git svn init https://svn.osgeo.org/grass/grass-promo
git svn --authors-file=${SCRIPTPATH}/AUTHORS.txt fetch
