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

function create_zip {
    echo "Creating zip..."
    cd $WWWDIR
    rm wingrass.zip
    zip wingrass.zip grass64 grass70 grass71 -r -q
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin:/c/OSGeo4W/bin

if test -z $1 ; then
    # daily builds
    ### copy 64 6.4.5svn
    ### copy 65
    copy 70 7.0.2svn
    copy 71 7.1.svn
    # releases
    copy_addon 644      6.4.4
    copy_addon 700      7.0.0
    copy_addon 701      7.0.1
    copy_addon 702RC2   7.0.2RC2
else
    copy $1 $2
fi

create_zip

exit 0
