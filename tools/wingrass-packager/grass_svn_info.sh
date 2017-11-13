#!/bin/sh
# Update SVN version info
#
# Options:
#  - platform (32 or 64)
#  - src postfix, eg. '_trunk'
#  - pkg patch number

SRC=usr/src
PACKAGEDIR=mswindows/osgeo4w/package
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

function update {
    GRASS_DIR=$1
    DST_DIR=$2
    PATCH_NUM=$3

    SRC_PATH=/c/msys${PLATFORM}/$SRC/$GRASS_DIR
    DEST_PATH=${HOME}/${DST_DIR}/${PLATFORM_DIR}
    
    cd $SRC_PATH

    REV=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    if test -z $PATCH_NUM ; then
	NUM=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`
	if [ "x$NUM" = "x" ]; then
	    NUM=1
	fi
    else
	NUM=$PATCH_NUM
    fi
    
    exec 3<include/VERSION 
    read MAJOR <&3 
    read MINOR <&3 
    read PATCH <&3 
    VERSION=$MAJOR.$MINOR.$PATCH
    
    if [[ "$PATCH" == *svn* ]] ; then
	TYPE="Devel"
    else
	TYPE="Release"
    fi
    sed -e "s/BINARY_REVISION \"1\"/BINARY_REVISION \"$NUM\"/g" \
	-e "s/INSTALLER_TYPE \"Devel\"/INSTALLER_TYPE \"$TYPE\"/g" \
	$DEST_PATH/GRASS-Installer.nsi > tmp
    mv tmp $DEST_PATH/GRASS-Installer.nsi
    cp error.log $DEST_PATH

    create_log $MAJOR$MINOR $REV $NUM
}

function create_log {
    VERSION=$1
    REV=$2
    PATCH=$3
    
    cd ${HOME}/grass${VERSION}/${PLATFORM_DIR}
    LOG_DIR=log-r$2-$3
    
    mkdir -p $LOG_DIR
    cp osgeo4w/package.log $LOG_DIR/
    cp error.log $LOG_DIR/
}

if test -z $2 ; then
    # dev packages
    ### update grass64_release grass64
    ### update grass70_release grass70
    update grass72_release grass72
    update grass74_release grass74    
    update grass_trunk     grass75
else
    update grass$2         grass$2 $3
fi

exit 0
