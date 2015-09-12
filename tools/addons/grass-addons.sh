#!/bin/sh

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

    update_manual 7 0
    update_manual 6 4
}

recompile_grass() {
    cd $DIR

    for gdir in "grass70_release" "grass64_release" ; do
	cd $gdir
        echo "Recompiling $gdir..." 1>&2
	svn up
	make distclean >/dev/null 2>&1
	if [ $gdir = "grass64_release" ] ; then 
	    num=6
	else
	    num=7
	fi
	$DIR/configures.sh grass$num >/dev/null 2>&1
	make >/dev/null 2>&1
        cat error.log 1>&2
        if [ "$?" != 0 ]; then
            exit 1
        fi
	cd ..
    done
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

if [ "$1" = "c" ] || [ "$2" = "c" ] ; then
    recompile_grass
fi

cd $DIR/grass-addons/ 

# update
svn up || (svn cleanup && svn up)

# check last change
date_last=`svn info --incremental --xml | grep date | cut -d '>' -f2 | cut -d '<' -f1`
num_last=`date --date="$date_last" +%s`
num_now=`date -u +%s`
count=$(echo "($num_now - $num_last) / 60." | bc)

if [ "$count" -lt "$CHECK_EVERY_MIN" ] || [ "$1" = "f" ] ; then
    build_addons $1
    exit 0
fi

exit 1
