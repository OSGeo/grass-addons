#!/bin/sh
# Update SVN version info

SRC=/osgeo4w/usr/src
PACKAGEDIR=mswindows/osgeo4w/package
HOME=/c/Users/landa/grass_packager

function update {
    cd $SRC/$1
    REV=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    NUM=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`

    exec 3<include/VERSION 
    read MAJOR <&3 
    read MINOR <&3 
    read PATCH <&3 
    if [[ "$PATCH" == *svn* ]] ; then
	TYPE="Devel"
    else
	TYPE="Release"
    fi
    sed "s/SVN_REVISION \"36599\"/SVN_REVISION \"$REV\"/g" $HOME/$2/GRASS-Installer.nsi > tmp1
    sed "s/BINARY_REVISION \"1\"/BINARY_REVISION \"$NUM\"/g" tmp1 > tmp2
    sed "s/INSTALLER_TYPE \"Devel\"/INSTALLER_TYPE \"$TYPE\"/g" tmp2 > tmp3
    rm tmp1 tmp2
    mv tmp3 $HOME/$2/GRASS-Installer.nsi
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

update grass64_release grass64
update grass6_devel grass65
update grass_trunk grass70

exit 0
