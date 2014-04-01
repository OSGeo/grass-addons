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

    copy_addon $1 $2
}

function copy_addon {
    version=$1
    version_full=$2

    cd $HOME/grass$version

    echo "Copying AddOns for grass${version}..."
    
    if test -n "$2"; then
	ADDONDIR=$WWWDIR/grass${version:0:2}/addons/grass-$version_full
    else
	ADDONDIR=$WWWDIR/grass${version:0:2}/addons
    fi
        
    mkdir -p $ADDONDIR
    
    cp    addons/*zip addons/*.md5sum $ADDONDIR
    cp -r addons/logs                 $ADDONDIR
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

if test -z $1 ; then
    # daily builds
    copy 64 6.4.4svn
    ### copy 65
    copy 70 7.0.0svn
    copy 71
    # releases
    copy_addon 643      6.4.3
    copy_addon 700beta1 7.0.0beta1
else
    copy $1 $2
fi

exit 0
