#!/bin/bash

# This script builds addons modules (1) and creates tarballs of manual
# pages, logs (2) for publishing server, see related grass-addons-publish.sh
# script for details
#
# To be run on building server (see crontab.build)
#
# original author: Martin Landa

# version numbers
GRASS_VERSION_OLD="6 4"
GRASS_VERSION_STABLE="7 8"

DST=/var/www/grass
DIST=dist.x86_64-pc-linux-gnu
SRC=${HOME}/src/

run=`ps aux | grep "compile-addons.sh c" | wc -l`
if [ "$run" == "2" ]; then
    echo "stopped"
    exit 0
fi

${SRC}/grass-addons/utils/addons/compile-addons.sh "$1"

if [ $? != 0 ] ; then
    exit 0
fi

manuals() {
    HTMLDIR=addons
    mkdir $HTMLDIR
    for dir in `find . -maxdepth 1 -type d`; do
        if [ -d $dir/docs/html ] ; then
            for f in `pwd`/$dir/docs/html/*.html ; do 
                ${SRC}/grass-addons/utils/addons/update_manual.py $f https://grass.osgeo.org/grass${1}${2}/manuals `pwd`
            done
            cp -r $dir/docs/html/* $HTMLDIR/ 2>/dev/null
        fi
    done
    cp ${SRC}/grass${1}${2}/${DIST}/docs/html/grassdocs.css $HTMLDIR/
    cp ${SRC}/grass${1}${2}/${DIST}/docs/html/grass_logo.png $HTMLDIR/
    tar czf html.tar.gz $HTMLDIR
    rm -rf $HTMLDIR
}

promote() {
    major=$1
    minor=$2
    cd /tmp/.grass${major}/addons
    tar czf logs.tar.gz logs
    manuals $major $minor
    cp logs/* ${DST}/addons/grass${major}
    cp logs.tar.gz ${DST}/addons/grass${major}
    cp modules.xml ${DST}/addons/grass${major}
    cp html.tar.gz ${DST}/addons/grass${major}
}

promote $GRASS_VERSION_OLD
promote $GRASS_VERSION_STABLE

exit 0
