#!/bin/sh
# Copy GRASS OSGeo4W package
#
# Options:
#  - platform (32 or 64)
#  - pkg postfix, eg. '70'
#  - pkg version number
#  - pkg patch number

HOME=/c/Users/landa/grass_packager
PATH_ORIG=`echo $PATH`

if test -z "$1"; then
    echo "platform not specified"
    exit 1
fi
PLATFORM=$1
export PATH=/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:/c/osgeo4w${PLATFORM}/bin:${PATH}

function rsync_package {
    POSTFIX=$1
    VERSION=$2
    PATCH=$3

    if [ "$PLATFORM" = "32" ] ; then
	PLATFORM_DIR=x86
    else
	PLATFORM_DIR=x86_64
    fi
    
    dir=${HOME}/${PLATFORM_DIR}/grass${POSTFIX}/osgeo4w/package
    curr=`ls -t $dir/ 2>/dev/null | head -n1 | cut -d'-' -f4 | cut -d'.' -f1`
    if [ $? -eq 0 ]; then
	package=$curr
    else
	package=1
    fi

    if test -z $VERSION; then
	# daily builds
	cp $dir/grass*-$package*.tar.bz2 ${HOME}/${PLATFORM_DIR}/grass${POSTFIX}
    else
	# release
	cp $dir/grass*-$package*.tar.bz2 ${HOME}/${PLATFORM_DIR}/grass${POSTFIX}/grass-${VERSION}-${PATCH}.tar.bz2
    fi
}

if test -z $2 ; then
    # dev packages
    ### rsync_package 64
    rsync_package 70
    rsync_package 71
else
    rsync_package $2 $3 $4
fi

exit 0
