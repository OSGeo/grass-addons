#!/bin/sh

WWW=/var/www
SRC=/var/www/wingrass
DST=/osgeo/download/osgeo4w/release/grass
OSGEOID=to_be_defined

rsync_grass() {
    rsync -avg --delete --delete-excluded \
	$SRC/grass$1/osgeo4w/ \
	${OSGEOID}@upload.osgeo.org:$DST/grass$1-dev
}

rm_7() {
    for f in `find $SRC/grass$1/WinGRASS* -mtime +7`; do
	rm -rfv $f
    done
    for f in `find $SRC/grass$1/osgeo4w/grass*.tar.bz2 -mtime +7`; do
	rm -rfv $f
    done
}

update_setup() {
    file=$SRC/grass$1/osgeo4w/setup.hint
    pattern=$SRC/grass$1/osgeo4w/*[0-9].tar.bz2
    
    curr=`ls -r -w1 $pattern | head -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
    prev=`ls -r -w1 $pattern | head -n2 | tail -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
    version=`grep curr $file | cut -d':' -f2 | cut -d'-' -f1 | tr -d ' '`
    
    sed -e "s/curr:.*/curr: ${version}-$curr/" \
	-e "s/prev:.*/prev: ${version}-$prev/" -i $file
}

addons_index() {
    cd $SRC/grass$1/addons
    if [ $1 = "64" ] ; then
	for d in $(find . -mindepth 1 -maxdepth 1 -type d) ; do
	    cd $d/logs
	    if [ -f "ALL.html" ] ; then
		mv ALL.html index.html
	    fi
	    cd ../..
	done
    else
	cd logs
	if [ -f "ALL.html" ] ; then
	    mv ALL.html index.html
	fi
    fi
}

report() {
    VERSION=$1
    cd $SRC/grass${VERSION}/logs
    last_log=`ls -t -w1 . | head -n1`
    if [ -d $last_log ] ; then
	cat $last_log/error.log 1>&2
    fi
}

# geo1 (win) -> geo101
cd $WWW
wget -r -nH --no-parent --reject="index.html*" -l5 \
   http://geo1.fsv.cvut.cz/wingrass/

# move ALL.html -> index.html
addons_index 64
addons_index 65
addons_index 70

# remove old packages
rm_7 64
rm_7 65
rm_7 70

# update setup.ini
update_setup 64
update_setup 65
update_setup 70

# geo101 -> upload.osgeo.org
rsync_grass 64
rsync_grass 65
rsync_grass 70

# promote changes
wget -q -O- http://upload.osgeo.org/cgi-bin/osgeo4w-regen.sh
wget -q -O- http://upload.osgeo.org/cgi-bin/osgeo4w-promote.sh

report 64
report 65
report 70

exit 0
