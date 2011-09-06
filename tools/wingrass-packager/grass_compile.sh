#!/bin/sh
# Compile GRASS 6.4, 6.5 and 7.0 (update source code from SVN repository)

SRC=/osgeo4w/usr/src

function update {
    echo "Updating $1..."     
    cd $SRC/$1
    svn up || (svn cleanup && svn up)
}

function compile {
    echo "Compiling $1..."
    cd $SRC/$1
    rm -f mswindows/osgeo4w/configure-stamp
    svn up || (svn cleanup && svn up)
    ./mswindows/osgeo4w/package.sh $2
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

# empty for native installer
PACKAGE=$1

update grass_addons

compile grass64_release $PACKAGE
compile grass6_devel $PACKAGE
compile grass_trunk $PACKAGE

exit 0
