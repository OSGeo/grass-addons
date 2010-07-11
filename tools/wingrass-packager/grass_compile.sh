#!/bin/sh
# Compile GRASS versions

SRC=/osgeo4w/usr/src

function compile {
    cd $SRC/$1
    make distclean
    svn up
    ./mswindows/osgeo4w/package.sh
}

compile grass64_release
compile grass6_devel
compile grass_trunk

exit 0
