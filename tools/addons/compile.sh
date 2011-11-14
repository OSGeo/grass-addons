#!/bin/sh

if [ -z "$3" ]; then
    echo "usage: $0 svn_path topdir addons_path"
    echo "eg. $0 ~/src/grass-addons/grass7/ ~/src/grass_trunk/dist.i686-pc-linux-gnu/ ~/.grass7/addons"
    exit 1
fi

SVN_PATH="$1"
TOPDIR="$2"
ADDON_PATH="$3"

rm -rf $ADDON_PATH
mkdir  $ADDON_PATH

cd $SVN_PATH

mkdir $ADDON_PATH/log
touch $ADDON_PATH/make.log

for c in "display" "general" "imagery" "raster" "vector"; do
    if [ ! -d $c ]; then
	continue
    fi
    cd $c
    for m in `ls -d */ 2>/dev/null` ; do
	m="${m%%/}"
	echo "Compiling $m..."
	cd $m
	make MODULE_TOPDIR=$TOPDIR \
	    BIN=$ADDON_PATH/bin \
	    HTMLDIR=$ADDON_PATH/docs/html \
	    MANDIR=$ADDON_PATH/man/man1 \
	    SCRIPTDIR=$ADDON_PATH/scripts \
	    ETC=$ADDON_PATH/etc \
	    MANIFEST= WINDRES= MANIFEST_OBJ= >$ADDON_PATH/log/${m}.log 2>&1
	if [ `echo $?` -eq 0 ] ; then
	    printf "%-30s%s\n" "$c/$m" "SUCCESS" >> $ADDON_PATH/make.log
	else
	    printf "%-30s%s\n" "$c/$m" "FAILED" >> $ADDON_PATH/make.log
	fi
	cd ..
    done
    cd ..
done

exit 0
