#!/bin/sh
# Update SVN version info

SRC=/usr/src
PACKAGEDIR=mswindows/osgeo4w/package
HOME=/c/Users/landa/grass_packager

function update {
    if [ "$1" = "grass_trunk" ] ; then
	cd /c/osgeo4w_g7/$SRC/$1
    else
	cd /c/osgeo4w/$SRC/$1
    fi
    
    REV=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    if test -z $4 ; then
	NUM=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`
	if [ "x$NUM" = "x" ]; then
	    NUM=1
	fi
    else
	NUM=$4
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
	$HOME/$2/GRASS-Installer.nsi > tmp
    mv tmp $HOME/$2/GRASS-Installer.nsi

    create_log $SRC/$1 $2 $REV $NUM
}

function create_log {
    cd $HOME/$2
    LOG_DIR=log-r$3-$4
    mkdir -p $LOG_DIR
    cp osgeo4w/package.log $LOG_DIR/
    cp error.log $LOG_DIR/
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

if test -z $1 ; then
    # dev packages
    update grass64_release grass64
    update grass6_devel    grass65
    update grass_trunk     grass70
else
    update grass$1         grass$1 $2
fi

exit 0
