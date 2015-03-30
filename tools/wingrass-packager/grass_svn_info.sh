#!/bin/sh
# Update SVN version info

SRC=/usr/src
PACKAGEDIR=mswindows/osgeo4w/package
HOME=/c/Users/landa/grass_packager

function update {
    if [ "$1" = "grass_trunk" ] ; then
	SRC_PATH=/c/osgeo4w/$SRC/$1
    else
	SRC_PATH=/c/osgeo4w/$SRC/$1
    fi
    DEST_PATH=$HOME/$2
    
    cd $SRC_PATH

    REV=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    if test -z $3 ; then
	NUM=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`
	if [ "x$NUM" = "x" ]; then
	    NUM=1
	fi
    else
	NUM=$3
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
    cd $HOME/grass$1
    LOG_DIR=log-r$2-$3
    
    mkdir -p $LOG_DIR
    cp osgeo4w/package.log $LOG_DIR/
    cp error.log $LOG_DIR/
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:/c/subversion/bin/svn

VERSION=$1
NUM=$2

if test -z $VERSION ; then
    # dev packages
    ### update grass64_release grass64
    ### update grass6_devel    grass65
    ### update grass70_release grass70
    update grass_trunk     grass71
else
    update grass$VERSION   grass$VERSION $NUM
fi

exit 0
