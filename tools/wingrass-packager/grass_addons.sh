#!/bin/sh
# Compile AddOns GRASS 6.4, 6.5 and 7.0

SVN_PATH=/c/osgeo4w/usr/src/grass_addons
GISBASE_PREFIX=/c/osgeo4w/usr/src
ADDON_PREFIX=/c/Users/landa/grass_packager

cd $SVN_PATH
svn up || (svn cleanup && svn up)

function compile {
    path=`echo $PATH`
    export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:$2/dist.i686-pc-mingw32/bin:$2/dist.i686-pc-mingw32/scripts
    rm -rf $3
    $SVN_PATH/tools/addons/compile.sh $1 $2 $3 1
    cd $3
    for d in `ls -d */`; do
	mod=${d%%/}
	if [ $mod == "log" ] ; then
	    continue
	fi
	cd $mod
	zip -r $mod.zip *
	mv $mod.zip ..
	cd ..
	md5sum $mod.zip > ${mod}.md5sum
    done
    export PATH=$path
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:/c/OSGeo4W/bin
export PYTHONHOME=/c/OSGeo4W/apps/Python25

compile $SVN_PATH/grass6 $GISBASE_PREFIX/grass6_devel $ADDON_PREFIX/grass65/addons

compile $SVN_PATH/grass7 $GISBASE_PREFIX/grass_trunk  $ADDON_PREFIX/grass70/addons

exit 0
