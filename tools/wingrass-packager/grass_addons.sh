#!/bin/sh
# Compile AddOns GRASS versions

SVN_PATH=/c/osgeo4w/usr/src/grass_addons
GISBASE_PATH=/c/osgeo4w/usr/src
ADDON_PATH=/c/Users/landa/grass_packager

PATH_ORIG=`echo $PATH`

(cd $SVN_PATH && \
 export PATH=$PATH_ORIG:/c/osgeo4w$3/apps/msys/bin:/c/Subversion/bin && \
 svn up || (svn cleanup && svn up) \
)

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
    export PATH=$PATH:/c/OSGeo4W$4/apps/msys/bin:/c/OSGeo4W$4/bin:$2/dist.i686-pc-mingw32/bin:$2/dist.i686-pc-mingw32/scripts:/c/subversion/bin/svn
    export PYTHONHOME=/c/OSGeo4W$4/apps/Python27

    rm -rf $3
    $SVN_PATH/tools/addons/compile.sh $1 $2 $3 1
    cd $3
    for d in `ls -d */`; do
	mod=${d%%/}
	if [ $mod == "logs" ] ; then
	    continue
	fi
	cd $mod
	echo $mod
	for f in `ls bin/*.bat 2> /dev/null` ; do
	    echo $f
	    if [ `echo $1 | sed -e 's/\(^.*\)\(.$\)/\2/'` = "6" ] ; then
		replace_gisbase="GRASS_ADDON_PATH"
	    else
		replace_gisbase="GRASS_ADDON_BASE"
	    fi
	    sed "s/GISBASE/$replace_gisbase/" $f > tmp
	    mv tmp $f
	done
	# if [ `echo $1 | sed -e 's/\(^.*\)\(.$\)/\2/'` = "6" ] ; then
	#     tidy_citizen
	# fi
	zip -r $mod.zip *
	mv $mod.zip ..
	cd ..
	md5sum $mod.zip > ${mod}.md5sum
    done
    export PATH=$PATH_ORIG
}

export LANGUAGE=C

if test -z $1 ; then
    ### compile $SVN_PATH/grass6 $GISBASE_PATH/grass644        $ADDON_PATH/grass644/addons
    ### compile $SVN_PATH/grass6 $GISBASE_PATH/grass64_release $ADDON_PATH/grass64/addons
    compile $SVN_PATH/grass7 $GISBASE_PATH/grass700        $ADDON_PATH/grass700/addons
    compile $SVN_PATH/grass7 $GISBASE_PATH/grass701        $ADDON_PATH/grass701/addons
    compile $SVN_PATH/grass7 $GISBASE_PATH/grass702        $ADDON_PATH/grass702/addons
    compile $SVN_PATH/grass7 $GISBASE_PATH/grass70_release $ADDON_PATH/grass70/addons
    compile $SVN_PATH/grass7 $GISBASE_PATH/grass_trunk     $ADDON_PATH/grass71/addons
else
    compile $SVN_PATH/grass6 $GISBASE_PATH/grass$1         $ADDON_PATH/grass$1/addons
fi

exit 0
