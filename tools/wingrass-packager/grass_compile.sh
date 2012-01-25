#!/bin/sh
# Compile GRASS 6.4, 6.5 and 7.0 (update source code from SVN repository)

SRC=/osgeo4w/usr/src
PACKAGEDIR=mswindows/osgeo4w/package

function rm_package_7 {
    for f in `/c/OSGeo4W/apps/msys/bin/find $PACKAGEDIR/grass*.tar.bz2 -mtime +7 2>/dev/null`; do
        rm -rfv $f
    done
}

function compile {
    cd $SRC/$1
    svn up || (svn cleanup && svn up)
    
    rm_package_7 
    curr=`ls -t $PACKAGEDIR/ 2>/dev/null | head -n1 | cut -d'-' -f5 | cut -d'.' -f1`
    if [ $? -eq 0 ]; then
	num=$(($curr+1))
    else
	num=1
    fi
    rev=`svn info | grep 'Last Changed Rev:' | cut -d':' -f2 | tr -d ' '`
    package="r$rev-$num"
    
    echo "Compiling $1 ($package)..."
    rm -f mswindows/osgeo4w/configure-stamp
    ./mswindows/osgeo4w/package.sh $package $2
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

compile grass64_release 64-dev
compile grass6_devel 65-dev
compile grass_trunk 70-dev

exit 0
