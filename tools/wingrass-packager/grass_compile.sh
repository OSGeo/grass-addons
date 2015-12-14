#!/bin/sh
# Compile GRASS versions (update source code from SVN repository)
#
# Options:
#  - platform (32 or 64)
#  - src postfix, eg. '_trunk'
#  - pkg postfix, eg. '-daily'

SRC_DIR=usr/src
PACKAGEDIR=mswindows/osgeo4w/package

if test -z "$1"; then
    echo "platform not specified"
    exit 1
fi
PLATFORM=$1
export PATH=/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:/c/osgeo4w${PLATFORM}/bin:${PATH}

function rm_package_7 {
    for f in `/c/osgeo4w$1/apps/msys/bin/find $PACKAGEDIR/grass*.tar.bz2 -mtime +7 2>/dev/null`; do
        rm -rfv $f
    done
}

function compile {
    GRASS_DIR=$1
    PACKAGE_POSTFIX=$2

    cd /c/msys${PLATFORM}/$SRC_DIR/$GRASS_DIR
    svn up || (svn cleanup && svn up)
    
    rm_package_7 $PLATFORM
    curr=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`
    if [ $? -eq 0 ]; then
	num=$(($curr+1))
    else
	num=1
    fi
    rev=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    package="r$rev-$num"
    
    echo "Compiling ${PLATFORM}bit $GRASS_DIR ($package)..."
    rm -f mswindows/osgeo4w/configure-stamp
    PACKAGE_PATCH=$package PACKAGE_POSTFIX=$PACKAGE_POSTFIX OSGEO4W_POSTFIX=$PLATFORM ./mswindows/osgeo4w/package.sh
}

if test -z $2 ; then
    # dev packages
    ### compile grass64_release 64-dev 
    compile grass70_release -dev
    compile grass_trunk     -daily
else
    compile grass$2         $3 
fi

exit 0
