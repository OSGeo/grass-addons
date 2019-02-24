#!/bin/sh

SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
SCRIPTPATH=`dirname $SCRIPT`

fetch() {
    DIR=$1
    OPT=$2
    RANGE=$3
    
    rm -rf $DIR
    mkdir $DIR
    cd $DIR
    repo=`echo $1 | sed 's/-fetch//g' | sed 's/-legacy//g'`
    # git svn init $OPT https://svn.osgeo.org/grass/$repo
    git svn init $OPT file:///opt/osgeo/svn/repos/grass/$repo
    git svn $RANGE --authors-file=${SCRIPTPATH}/AUTHORS.txt fetch
    cd ..
}

fetch "grass-fetch" "--stdlayout" "-r31142:75000"
fetch "grass-legacy-fetch" "--stdlayout"
fetch "grass-addons-fetch"
fetch "grass-promo-fetch"
