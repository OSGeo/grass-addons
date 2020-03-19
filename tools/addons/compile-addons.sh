#!/bin/bash

# updated for new CMS path MN 8/2015

DIR=$HOME/src
# XMLDIR=/var/www/grass/grass-cms/addons/
MANDIR=/var/www/grass/grass-cms/
XMLDIR=/var/www/grass/addons/
#??? MANDIR=/var/www/grass
CHECK_EVERY_MIN=15

if [ ! -d "$XMLDIR" ]; then
    mkdir -p $XMLDIR
fi

build_addons() {
    cd tools/addons/ 
    ./compile-xml.sh $XMLDIR
    for version in 6 7 ; do
    	cd /tmp/.grass${version}/addons/
    	cp modules.xml $XMLDIR/grass${version}
    	rsync -ag --delete logs $XMLDIR/grass${version}
    	cd $XMLDIR/grass${version}/logs
    done

    update_manual 7 8
    update_manual 6 4
}

update_manual() {
    major=$1
    minor=$2
    echo "Updating manuals for GRASS ${major}.${minor}..."
    dst="$MANDIR/grass${major}${minor}/manuals/addons/"
    if [ ! -d $dst ] ; then
	mkdir -p $dst
        cd $dst
	wget http://grass.osgeo.org/grass${major}${minor}/manuals/grass_logo.png 
	wget http://grass.osgeo.org/grass${major}${minor}/manuals/grassdocs.css
    fi
    cd /tmp/.grass${major}/addons/
    for m in $(ls -d */) ; do 
        if [ `ls ${m}docs/html/ -w1 2>/dev/null | wc -l` -gt 0 ] ; then
	    cp ${m}docs/html/* $dst
        fi
    done
}

export GRASS_SKIP_MAPSET_OWNER_CHECK="1"

cd $DIR/grass-addons

# update
git pull

# check last change
date_last=`git log -1 --format=%ci | awk '{print $1"T"$2"Z"}'`
date_last_modified=`ls -d /tmp/.grass7/addons/ -l --time-style=full-iso | cut -d ' ' -f 6,7 | awk '{print $1"T"$2"Z"}'`
unix_date_last=$(date -d "${date_last}" "+%s")
unix_date_last_modified=$(date -d "${date_last_modified}" "+%s")

if [ "$unix_date_last" -gt "$unix_date_last_modified" ] || [ "$1" = "f" ] ; then
    echo "TIME DIFF: $date_last / $date_last_modified"
    build_addons $1
    exit 0
fi

exit 1
