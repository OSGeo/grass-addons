#!/bin/sh

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

# update GRASS Addons SVN
(cd ..; git pull)

# compile AddOns for GRASS 7 and GRASS 6.5
compile ../../grass7 ~/src/grass78/dist.x86_64-pc-linux-gnu /tmp/.grass7/addons
compile ../../grass6 ~/src/grass64/dist.x86_64-pc-linux-gnu /tmp/.grass6/addons

# create XML file for AddOns
build_xml /tmp/.grass7/addons 7
build_xml /tmp/.grass6/addons 6

exit 0
