#!/bin/sh
# Copy binaries to www server
#
# Options:
#  - platform (32 or 64)
#  - src version, eg. 700
#  - version, eg. 7.0.1

WWWDIR=/c/inetpub/wwwroot/wingrass
HOME=/c/Users/landa/grass_packager
if test -z "$1"; then
    echo "platform not specified"
    exit 1
fi
PLATFORM=$1
export PATH=/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:/c/osgeo4w${PLATFORM}/bin:${PATH}

if [ "$PLATFORM" = "32" ] ; then
    PLATFORM_DIR=x86
else
    PLATFORM_DIR=x86_64
fi

function copy {
    DIR=$1
    VERSION=$2
    
    cd ${HOME}/grass${DIR}/${PLATFORM_DIR}

    if [ ! -d ${WWWDIR}/grass${DIR} ] ; then
	mkdir ${WWWDIR}/grass${DIR}
    fi

    DST_DIR=${WWWDIR}/grass${DIR}/${PLATFORM_DIR}

    rm -rf $DST_DIR
    mkdir  $DST_DIR
    
    cp    WinGRASS*.exe* $DST_DIR
    
    mkdir ${DST_DIR}/osgeo4w
    cp    grass*.tar.bz2 ${DST_DIR}/osgeo4w
    
    mkdir ${DST_DIR}/logs
    cp -r log-r*         ${DST_DIR}/logs

    copy_addon $DIR $VERSION
}

function copy_addon {
    DIR=$1
    VERSION=$2
    
    cd ${HOME}/grass${DIR}/${PLATFORM_DIR}

    if test -n "$VERSION"; then
	ADDONDIR=${WWWDIR}/grass${DIR:0:2}/${PLATFORM_DIR}/addons/grass-$VERSION
    else
	ADDONDIR=${WWWDIR}/grass${DIR:0:2}/${PLATFORM_DIR}/addons
    fi
        
    mkdir -p $ADDONDIR
    
    cp    addons/*zip addons/*.md5sum $ADDONDIR
    cp -r addons/logs                 $ADDONDIR
}

function create_zip {
    cd $WWWDIR
    zipfile=wingrass.zip
    rm $zipfile
    zip $zipfile grass* -r -q
}

echo "... ($PLATFORM_DIR)"

if test -z $2 ; then
    # daily builds
    ### copy 64 6.4.5svn
    ### copy 65
    copy        70       7.0.3svn
    copy        71       7.1.svn
    # releases (TODO: enable later)
    #copy_addon 644      6.4.4
    #copy_addon 700      7.0.0
    #copy_addon 701      7.0.1
    #copy_addon 702      7.0.2
    copy_addon 703RC2    7.0.3RC2
else
    copy        $2       $3
fi

create_zip

exit 0
