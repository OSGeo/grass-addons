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

    update_manual 7 6
    update_manual 6 4
}

recompile_grass() {
    source $DIR/grass-p2/venv/bin/activate
    gdir=$DIR/grass-p2/r${1}

    cd $gdir
    echo "Recompiling $gdir..." 1>&2
    git pull
    make distclean     >/dev/null 2>&1
    OPTS="--enable-largefile --with-blas --with-bzlib --with-cairo --with-cxx \
          --with-freetype --with-freetype-includes=/usr/include/freetype2 --with-gdal --with-geos --with-lapack \
          --with-liblas=/usr/bin/liblas-config --with-motif -with-netcdf --with-nls --with-odbc --with-openmp \
          --with-postgres --with-postgres-includes=/usr/include/postgresql --with-proj-share=/usr/share/proj \
          --with-python --with-readline --with-sqlite --with-x"
    if [ "$1" = "64" ]; then
        OPTS+="--with-tcltk --with-tcltk-includes=/usr/include/tcl8.5/"
    else
        OPTS+="--with-wxwidgets=/usr/bin/wx-config --with-zstd"
    fi
    ./configure $OPTS >/dev/null 2>&1
    make              >/dev/null 2>&1
    cat error.log 1>&2
    if [ "$?" != 0 ]; then
        exit 1
    fi
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
    recompile_grass 64
    recompile_grass 76
fi

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
