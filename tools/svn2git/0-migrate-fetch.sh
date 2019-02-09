#!/bin/sh

# core repo
DIR=grass-fetch
mkdir $DIR ; cd $DIR
git svn init --stdlayout https://svn.osgeo.org/grass/grass
git svn --authors-file=../AUTHORS.txt fetch

# addons repo
DIR=grass-addons-fetch
mkdir $DIR ; cd $DIR
git svn init https://svn.osgeo.org/grass/grass-addons
git svn --authors-file=../AUTHORS.txt fetch

# promo
DIR=grass-promo-fetch
mkdir $DIR ; cd $DIR
git svn init https://svn.osgeo.org/grass/grass-promo
git svn --authors-file=../AUTHORS.txt fetch
