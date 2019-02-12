#!/bin/sh

SCRIPT=`realpath $0` # realpath is a separate package and doesn't need to be installed
SCRIPTPATH=`dirname $SCRIPT`

function fetch() {
    DIR=$1
    OPT=$2
    
    mkdir $DIR
    cd $DIR
    git svn init $OPT https://svn.osgeo.org/grass/grass
    git svn --authors-file=${SCRIPTPATH}/AUTHORS.txt fetch
    cd ..
}

fetch "grass-fetch" "--stdlayout"
fetch "grass-addons-fetch"
fetch "grass-promo-fetch"
