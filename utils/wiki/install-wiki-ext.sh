#!/bin/sh

WIKI=/osgeo/grass/grass-wiki
EXT=$1

if test -z "$EXT" ; then
    echo "Usage: ext"
    exit 1
fi

cd $WIKI/extensions
git clone https://gerrit.wikimedia.org/r/p/mediawiki/extensions/${EXT}.git

exit 0
