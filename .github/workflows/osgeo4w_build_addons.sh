#!/bin/sh
# Compile GRASS GIS Addons
#
# Options:
#  - src postfix, eg. '_trunk'

# export PATH=/c/osgeo4w${PLATFORM}/bin:/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:${PATH}
export PATH=/c/msys64/usr/bin:${PATH}
# export PYTHONPATH=
export LANGUAGE=C
export OSGEO4W_ROOT_MSYS="/c/OSGeo4W"

SRC_PATH=${ADDON_PATH}/src
GISBASE_PATH=/c/msys64/usr/src
TARGET_PATH=/c/grass_addons

fetchenv() {
    local IFS
    IFS=
    batch=$1
    shift
    srcenv=$(mktemp /tmp/srcenv.XXXXXXXXXX)
    dstenv=$(mktemp /tmp/dstenv.XXXXXXXXXX)
    diffenv=$(mktemp /tmp/diffenv.XXXXXXXXXX)
    args="$@"
    cmd.exe //c set >$srcenv
    cmd.exe //c "call `cygpath -w $batch` $args \>nul 2\>nul \& set" >$dstenv
    diff -u $srcenv $dstenv | sed -f ${SRC_GRASS}/mswindows/osgeo4w/envdiff.sed >$diffenv
    . $diffenv
    PATH=$PATH:/usr/bin:/mingw64/bin/:$PWD/mswindows/osgeo4w/lib:$PWD/mswindows/osgeo4w:/c/windows32/system32:/c/windows:/c/windows32/system32:/c/windows
    rm -f $srcenv $dstenv $diffenv
}

function compile {
    SRC_ADDONS=${GISBASE_PATH}/grass${1:0:1}-addons/src
    SRC_GRASS=${GISBASE_PATH}/grass$1
    DST_DIR=${TARGET_PATH}/grass$1/addons

    (cd $SRC_ADDONS; git pull)
    fetchenv $OSGEO4W_ROOT_MSYS/bin/o4w_env.bat
    export PATH=${PATH}:/c/msys64/usr/bin:/c/msys64/mingw64/bin
    grass_version=`echo $SRC_GRASS | cut -d '/' -f6 | sed 's/grass//g'`

    rm -rf $DST_DIR
    ls `pwd`
    ./osgeo4w_compile_addons.sh $SRC_ADDONS $SRC_GRASS $DST_DIR 1
    cd $DST_DIR
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
	zip -r $mod.zip *
	mv $mod.zip ..
	cd ..
	md5sum $mod.zip > ${mod}.md5sum
    done
}

if test -z $1 ; then
    while read release; do
        compile $release
    done < releases.csv
else
    compile $1
fi

exit 0
