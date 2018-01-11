#!/bin/sh
# Compile GRASS GIS Addons
#
# Options:
#  - platform (32 or 64)
#  - src postfix, eg. '_trunk'

if test -z "$1"; then
    echo "platform not specified"
    exit 1
fi
PLATFORM=$1
export PATH=/c/osgeo4w${PLATFORM}/bin:/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:${PATH}
export GRASS_PYTHON=/c/OSGeo4W${PLATFORM}/pythonw.exe
export GRASS_PYTHONPATH=/c/OSGeo4W${PLATFORM}/apps/Python27/Lib
export PYTHONHOME=/c/OSGeo4W${PLATFORM}/apps/Python27
export LANGUAGE=C

SVN_PATH=/c/msys${PLATFORM}/usr/src/grass_addons
GISBASE_PATH=/c/msys${PLATFORM}/usr/src
ADDON_PATH=/c/Users/landa/grass_packager
if [ "$PLATFORM" = "32" ] ; then
    PLATFORM_DIR=x86
else
    PLATFORM_DIR=x86_64
fi

cd $SVN_PATH
svn up || (svn cleanup && svn up)

function compile {
    SRC_ADDONS=$1
    SRC_GRASS=$2
    DST_DIR=$3

    rm -rf $DST_DIR
    $SVN_PATH/tools/addons/compile.sh $SRC_ADDONS $SRC_GRASS $DST_DIR 1
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

if test -z $2 ; then
    ### compile ${SVN_PATH}/grass6 ${GISBASE_PATH}/grass644        ${ADDON_PATH}/grass644/addons
    ### compile ${SVN_PATH}/grass6 ${GISBASE_PATH}/grass64_release ${ADDON_PATH}/grass64/addons
    # TODO: enable later
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass700        ${ADDON_PATH}/grass700/addons
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass701        ${ADDON_PATH}/grass701/addons
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass702        ${ADDON_PATH}/grass702/addons
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass703        ${ADDON_PATH}/grass703/${PLATFORM_DIR}/addons
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass704        ${ADDON_PATH}/grass704/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass705        ${ADDON_PATH}/grass705/${PLATFORM_DIR}/addons
    # compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass70_release ${ADDON_PATH}/grass70/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass720        ${ADDON_PATH}/grass720/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass721        ${ADDON_PATH}/grass721/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass722        ${ADDON_PATH}/grass722/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass72_release ${ADDON_PATH}/grass72/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass740RC2     ${ADDON_PATH}/grass740RC2/${PLATFORM_DIR}/addons
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass74_release ${ADDON_PATH}/grass74/${PLATFORM_DIR}/addons    
    compile ${SVN_PATH}/grass7 ${GISBASE_PATH}/grass_trunk     ${ADDON_PATH}/grass75/${PLATFORM_DIR}/addons
else
    compile ${SVN_PATH}/grass6 ${GISBASE_PATH}/grass$2         ${ADDON_PATH}/grass$2/${PLATFORM_DIR}/addons
fi

exit 0
