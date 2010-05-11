#!/bin/sh
# Update SVN version

SRC=/osgeo4w/usr/src
HOME=/c/Users/landa/grass_packager

function update {
    cd $SRC/$1
    REV=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    sed "s/_SVN_REVISION \"36599\"/_SVN_REVISION \"$REV\"/g" $HOME/$2/GRASS-Installer.nsi > tmp
    mv tmp $HOME/$2/GRASS-Installer.nsi
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

update grass64_release grass64
update grass6_devel grass65
update grass_trunk grass70

exit 0
