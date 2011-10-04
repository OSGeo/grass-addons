#!/bin/sh
# Copy GRASS OSGeo4W package

HOME=/c/Users/landa/grass_packager

function rsync_package {
    dir=$HOME/grass$1/osgeo4w/package
    curr=`ls -t $dir/ 2>/dev/null | head -n1 | cut -d'-' -f3 | cut -d'.' -f1`
    if [ $? -eq 0 ]; then
	package=$curr
    else
	package=1
    fi

    cp $dir/grass*-$package-*.tar.bz2 $HOME/grass$1
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

rsync_package 64
rsync_package 65
rsync_package 70

exit 0
