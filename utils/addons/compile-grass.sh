#!/bin/bash

# version numbers
GRASS_VERSION_OLD="6 4"
GRASS_VERSION_STABLE="7 8"

DIR=$HOME/src

recompile_grass() {
    gdir=$DIR/grass${1}

    cd $gdir
    echo "Recompiling $gdir..." 1>&2
    git pull
    make distclean     >/dev/null 2>&1
    # TODO 2021: verify flags
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

# parse version numbers
G_OLD_MAJOR=`echo $GRASS_VERSION_OLD | cut -d' ' -f1`
G_OLD_MINOR=`echo $GRASS_VERSION_OLD | cut -d' ' -f2`
G_STABLE_MAJOR=`echo $GRASS_VERSION_STABLE | cut -d' ' -f1`
G_STABLE_MINOR=`echo $GRASS_VERSION_STABLE | cut -d' ' -f2`

recompile_grass ${G_OLD_MAJOR}${G_OLD_MINOR}
recompile_grass ${G_STABLE_MAJOR}${G_STABLE_MINOR}

exit 0
