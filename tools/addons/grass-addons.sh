#!/bin/sh

DIR=$HOME/src
WWWDIR=/osgeo/grass/grass-cms/addons/

build_addons() {
cd $DIR/grass-addons/ 

##revl=`svn info | grep 'Revision' | cut -d':' -f2 | tr -d ' '`
##revr=`svn info -rHEAD | grep 'Revision' | cut -d':' -f2 | tr -d ' '`
nup=`(svn up || (svn cleanup && svn up)) | wc -l`

###if [ "$revl" != "$revr" ] || [ "$1" = "f" ] ; then
if [ "$nup" -ne 1 ] || [ "$1" = "f" ] ; then
    ###svn up || (svn cleanup && svn up)

    cd tools/addons/ 
    ./compile-xml.sh
    for version in 6 7 ; do
    	cd $HOME/.grass${version}/addons/
    	cp modules.xml $WWWDIR/grass${version}/
    	rsync -ag --delete logs $WWWDIR/grass${version}/
    	cd $WWWDIR/grass${version}/logs
    	ln -sf ALL.html index.html
    done
fi
}

recompile_grass() {
    cd $DIR

    for gdir in "grass_trunk" "grass6_devel" "grass64_release" ; do
	cd $gdir
	svn up
	make distclean
	if [ $gdir = "grass_trunk" ] ; then 
	    num=7
	else
	    num=6
	fi
	$DIR/configures.sh grass$num
	make
	cd ..
    done
}

export GRASS_SKIP_MAPSET_OWNER_CHECK="1"

if [ "$1" = "c" ] || [ "$2" = "c" ] ; then
    recompile_grass
fi

build_addons $1

exit 0
