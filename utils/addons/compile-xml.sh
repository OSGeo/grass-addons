#!/bin/sh

GRASS_VERSION_OLD="6 4"
GRASS_VERSION_STABLE="7 8"

if test -z "$1" ; then
    echo "DEST not defined"
    exit 1
fi
DEST="$1"

compile() {
    ./compile.sh $1 $2 $3 1
}

build_xml() {
    ./build-xml.py $1
    cp $1/modules.xml $DEST/grass$2/
    cp -r $1/logs $DEST/grass$2/
}

# update GRASS Addons from git
(cd ..; git pull)

# parse version numbers
G_OLD_MAJOR=`echo $GRASS_VERSION_OLD | cut -d' ' -f1`
G_OLD_MINOR=`echo $GRASS_VERSION_OLD | cut -d' ' -f2`
G_STABLE_MAJOR=`echo $GRASS_VERSION_STABLE | cut -d' ' -f1`
G_STABLE_MINOR=`echo $GRASS_VERSION_STABLE | cut -d' ' -f2`

# compile AddOns for old and stable
compile ../../grass${G_STABLE_MAJOR} ~/src/grass${G_STABLE_MAJOR}${G_STABLE_MINOR}/dist.x86_64-pc-linux-gnu /tmp/.grass${G_STABLE_MAJOR}/addons
compile ../../grass${G_OLD_MAJOR} ~/src/grass${G_OLD_MAJOR}${G_OLD_MINOR}/dist.x86_64-pc-linux-gnu /tmp/.grass${G_OLD_MAJOR}/addons

# create XML file for AddOns
build_xml /tmp/.grass${G_STABLE_MAJOR}/addons ${G_STABLE_MAJOR}
build_xml /tmp/.grass${G_OLD_MAJOR}/addons ${G_OLD_MAJOR}

exit 0
