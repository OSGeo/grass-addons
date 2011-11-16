#!/bin/sh

compile() {
    ./compile.sh $1 $2 $3
}

build_xml() {
    ./build-xml.py $1
}

# recompile GRASS'es
### $HOME/src/update-grass.sh

# update GRASS Addons SVN
# WARNING: create symlinks in grass6 first!
(cd ..; svn up)

# compile AddOns for GRASS 7 and GRASS 6.5
compile ../../grass7 ~/src/grass_trunk/dist.x86_64-unknown-linux-gnu  ~/.grass7/addons
compile ../../grass6 ~/src/grass6_devel/dist.x86_64-unknown-linux-gnu ~/.grass6/addons

# create XML file for AddOns
build_xml ~/.grass7/addons
build_xml ~/.grass6/addons

exit 0
