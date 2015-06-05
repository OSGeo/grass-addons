#!/bin/sh
# Compile GRASS versions (update source code from SVN repository)

SRC=/usr/src
PACKAGEDIR=mswindows/osgeo4w/package
PATH_ORIG=`echo $PATH`

function rm_package_7 {
    for f in `/c/osgeo4w$1/apps/msys/bin/find $PACKAGEDIR/grass*.tar.bz2 -mtime +7 2>/dev/null`; do
        rm -rfv $f
    done
}

function compile {
    export PATH=$PATH_ORIG:/c/osgeo4w$3/apps/msys/bin:/c/Subversion/bin

    cd /c/osgeo4w$3/$SRC/$1
    svn up || (svn cleanup && svn up)
    
    rm_package_7 $3 
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
    ./mswindows/osgeo4w/package.sh $package $2 $3

    export PATH=$PATH_ORIG
}

if test -z $1 ; then
    # dev packages
    ### compile grass64_release 64-dev 
    ### compile grass6_devel    65-dev 
    compile grass70_release -dev 
    compile grass_trunk     -daily
else
    compile grass$1         $2
fi

exit 0
