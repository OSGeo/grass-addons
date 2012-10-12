#!/bin/sh

DIR=$HOME/src

build_addons() {
cd $DIR/grass-addons/ 

revl=`svn info | grep 'Revision' | cut -d':' -f2 | tr -d ' '`
revr=`svn info -rHEAD | grep 'Revision' | cut -d':' -f2 | tr -d ' '`

if [ "$revl" != "$revr" ] || [ "$1" = "f" ] ; then
    svn up || (svn cleanup && svn up)

    cd tools/addons/ 
    ./compile-xml.sh
else
    echo "$revl X $revr -> nothing to do"
fi
}

recompile_grass() {
    cd $DIR

    for dir in "grass_trunk" "grass6_devel" "grass64_release" ; do
	cd $dir
	svn up
	make distclean
	if [ $dir == "grass_trunk" ] ; then 
	    num=7
	else
	    num=6
	fi
	../configures.sh grass$num
	make
	cd ..
    done
}

#recompile_grass
build_addons $1

exit 0
