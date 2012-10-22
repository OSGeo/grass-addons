#!/bin/sh
# Compile AddOns GRASS 6.4, 6.5 and 7.0

SVN_PATH=/c/osgeo4w/usr/src/grass_addons
GISBASE_PREFIX=/c/osgeo4w/usr/src
ADDON_PREFIX=/c/Users/landa/grass_packager

cd $SVN_PATH
svn up || (svn cleanup && svn up)

# see http://lists.osgeo.org/pipermail/grass-dev/2011-December/056938.html
function tidy_citizen {
    # move script/ and bin/ to main dir
    mv bin/* .
    mv scripts/* .
    
    # move man/ into docs/
    mv man docs/
    
    # if empty, rmdir bin, etc, man, scripts
    rmdir bin etc scripts
}

function compile {
    path=`echo $PATH`
    export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:$2/dist.i686-pc-mingw32/bin:$2/dist.i686-pc-mingw32/scripts
    rm -rf $3
    $SVN_PATH/tools/addons/compile.sh $1 $2 $3 1
    cd $3
    for d in `ls -d */`; do
	mod=${d%%/}
	if [ $mod == "logs" ] ; then
	    continue
	fi
	cd $mod
	if [ -f bin/${mod}.bat ] ; then
	    sed "s/GISBASE/GRASS_ADDON_PATH/" bin/${mod}.bat > tmp
	    mv tmp bin/${mod}.bat
	fi
	# if [ `echo $1 | sed -e 's/\(^.*\)\(.$\)/\2/'` = "6" ] ; then
	#     tidy_citizen
	# fi
	zip -r $mod.zip *
	mv $mod.zip ..
	cd ..
	md5sum $mod.zip > ${mod}.md5sum
    done
    export PATH=$path
}

export PATH=/c/OSGeo4W/apps/msys/bin:/c/OSGeo4W/bin:$PATH
export PYTHONHOME=/c/OSGeo4W/apps/Python27
export LANGUAGE=C

if test -z $1 ; then
    # dev packages
    compile $SVN_PATH/grass6 $GISBASE_PREFIX/grass64_release $ADDON_PREFIX/grass64/addons
    compile $SVN_PATH/grass6 $GISBASE_PREFIX/grass6_devel    $ADDON_PREFIX/grass65/addons
    compile $SVN_PATH/grass7 $GISBASE_PREFIX/grass_trunk     $ADDON_PREFIX/grass70/addons
else
    compile $SVN_PATH/grass6 $GISBASE_PREFIX/grass$1         $ADDON_PREFIX/grass$1/addons
fi

exit 0
