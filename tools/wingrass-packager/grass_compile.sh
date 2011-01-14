#!/bin/sh
# Compile GRASS 6.4, 6.5 and 7.0 (update source code from SVN repository)

SRC=/osgeo4w/usr/src

function compile {
    cd $SRC/$1
    rm -f mswindows/osgeo4w/configure-stamp
    svn up || (svn cleanup && svn up)
    ./mswindows/osgeo4w/package.sh
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

compile grass64_release
compile grass6_devel
compile grass_trunk

exit 0
