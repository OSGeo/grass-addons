#!/bin/sh
# Creates release packages for OSGeo4W

HOME=/c/Users/landa/grass_packager

if test -z "$2" ; then
    echo "$0 dir num"
    exit 1
fi

SRC=$1
PACKAGE=$2

cd $SRC
#rm -f mswindows/osgeo4w/configure-stamp
./mswindows/osgeo4w/package.sh $PACKAGE


exit 0
