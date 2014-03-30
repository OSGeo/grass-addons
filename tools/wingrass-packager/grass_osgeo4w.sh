#!/bin/sh
# Copy GRASS OSGeo4W package

HOME=/c/Users/landa/grass_packager

function rsync_package {
    dir=$HOME/grass$1/osgeo4w/package
    curr=`ls -t $dir/ 2>/dev/null | head -n1 | cut -d'-' -f4 | cut -d'.' -f1`
    if [ $? -eq 0 ]; then
	package=$curr
    else
	package=1
    fi

    if test -z $2; then
	cp $dir/grass*-$package*.tar.bz2 $HOME/grass$1
    else
	cp $dir/grass*-$package*.tar.bz2 $HOME/grass$1/grass-$2-$3.tar.bz2
    fi
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

if test -z $1 ; then
    # dev packages
    rsync_package 64
    ### rsync_package 65
    rsync_package 70
    rsync_package 71
else
    rsync_package $1 $2 $3
fi

exit 0
