#!/bin/sh

if [ -z "$3" ]; then
    echo "usage: $0 path topdir version"
    echo "eg. $0 ~/src/grass-addons/grass7/ ~/src/grass_trunk/dist.i686-pc-linux-gnu/ 7"
    exit 1
fi

path="$1"
topdir="$2"
version="$3"

rm -r ~/.grass$version/addons
mkdir ~/.grass$version/addons

cd $path
for c in "display" "general" "imagery" "raster" "vector"; do
    if [ ! -d $c ]; then
	continue
    fi
    cd $c
    for m in `ls -d */ 2>/dev/null` ; do
	echo "Compiling $m..."
	cd $m
	make MODULE_TOPDIR=$topdir \
            BIN=~/.grass$version/addons/bin \
            HTMLDIR=~/.grass$version/addons/docs/html \
            MANDIR=~/.grass$version/addons/man/man1 \
            SCRIPTDIR=~/.grass$version/addons/scripts \
            ETC=~/.grass$version/addons/etc
	cd ..
    done
    cd ..
done

exit 0
