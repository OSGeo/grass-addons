#!/bin/sh

if [ -z "$3" ]; then
    echo "usage: $0 svn_path topdir addons_path [separate]"
    echo "eg. $0 ~/src/grass-addons/grass7/ ~/src/grass_trunk/dist.x86_64-unknown-linux-gnu ~/.grass7/addons"
    exit 1
fi

SVN_PATH="$1"
TOPDIR="$2"
ADDON_PATH="$3"

if [ -n "$4" ] ; then
    SEP=1 # useful for collecting files (see build-xml.py)
else
    SEP=0
fi

rm -rf $ADDON_PATH
mkdir  $ADDON_PATH

cd $SVN_PATH

mkdir $ADDON_PATH/log
touch $ADDON_PATH/make.log

echo "-----------------------------------------------------"
echo "AddOns '$ADDON_PATH'..."
echo "-----------------------------------------------------"
for c in "display" "general" "imagery" "raster" "vector"; do
    if [ ! -d $c ]; then
	continue
    fi
    cd $c
    for m in `ls -d */ 2>/dev/null` ; do
	m="${m%%/}"
	echo -n "Compiling $m..."
	cd $m
	if [ $SEP -eq 1 ] ; then
	    path=${ADDON_PATH}/$m
	else
	    path=$ADDON_PATH
	fi
	make MODULE_TOPDIR=$TOPDIR \
	    BIN=$path/bin \
	    HTMLDIR=$path/docs/html \
	    MANDIR=$path/man/man1 \
	    SCRIPTDIR=$path/scripts \
	    ETC=$path/etc \
	    MANIFEST= WINDRES= MANIFEST_OBJ= >$ADDON_PATH/log/${m}.log 2>&1
	if [ `echo $?` -eq 0 ] ; then
	    printf "%-30s%s\n" "$c/$m" "SUCCESS" >> $ADDON_PATH/make.log
	    echo " SUCCESS"
	else
	    printf "%-30s%s\n" "$c/$m" "FAILED" >> $ADDON_PATH/make.log
	    echo " FAILED"
	fi
	cd ..
    done
    cd ..
done

exit 0
