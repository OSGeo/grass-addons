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

    if test -n "$2"; then
	ADDONDIR=$WWWDIR/grass$1/addons/grass-$2
    else
	ADDONDIR=$WWWDIR/grass$1/addons
    fi
    mkdir -p $ADDONDIR
    
    cp    addons/*zip addons/*.md5sum $ADDONDIR
    cp -r addons/logs                 $ADDONDIR
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

if test -z $1 ; then
    # dev packages
    copy 64 6.4.3svn
    copy 65
    copy 70
else
    copy $1 $2
fi

exit 0
