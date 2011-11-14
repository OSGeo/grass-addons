#!/bin/sh
# Compile AddOns GRASS 6.4, 6.5 and 7.0

SVN_PATH=/c/osgeo4w/usr/src/grass_addons
GISBASE_PREFIX=/c/osgeo4w/usr/src
ADDON_PREFIX=/c/Users/landa/grass_packager

cd $SVN_PATH
#svn up

function compile {
    path=`echo $PATH`
    export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:$2/bin:$2/scripts    
    ./tools/addons/compile.sh $1 $2 $3
    export PATH=$path
}

compile $SVN_PATH/grass7 $GISBASE_PREFIX/grass_trunk/dist.i686-pc-mingw32 $ADDON_PREFIX/grass70/addons

exit 0
