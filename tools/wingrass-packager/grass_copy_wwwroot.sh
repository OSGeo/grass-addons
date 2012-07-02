#!/bin/sh
# Copy binaries to www server

WWWDIR=/c/inetpub/wwwroot/wingrass
HOME=/c/Users/landa/grass_packager

function copy {
    cd $HOME/grass$1

    echo "Copying grass$1..."
    
    rm -rf $WWWDIR/grass$1
    mkdir $WWWDIR/grass$1
    
    cp    WinGRASS*.exe* $WWWDIR/grass$1
    
    mkdir $WWWDIR/grass$1/osgeo4w
    cp    grass*.tar.bz2 $WWWDIR/grass$1/osgeo4w
    
    mkdir $WWWDIR/grass$1/logs
    cp -r log-r*         $WWWDIR/grass$1/logs

    mkdir $WWWDIR/grass$1/addons
    cp    addons/*zip addons/*.md5sum $WWWDIR/grass$1/addons
    cp -r addons/logs                 $WWWDIR/grass$1/addons
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

copy 64
copy 65
copy 70

exit 0
