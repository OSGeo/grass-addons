#!/bin/sh

WWW=/var/www
SRC=/var/www/wingrass
DST=/osgeo/download/osgeo4w

rsync_grass() {
    for p in x86 x86_64; do
	rsync -avg --delete --delete-excluded \
	    ${SRC}/${p}/grass${1}/osgeo4w/ \
	    martinl@upload.osgeo.org:$DST/${p}/release/grass/grass$2
    done
}

rm_7() {
    for p in x86 x86_64; do
	cd $p
	for f in `find $SRC/${p}/grass$1/WinGRASS* -mtime +7`; do
	    rm -rfv $f
	done
	for f in `find $SRC/${p}/grass$1/osgeo4w/grass*.tar.bz2 -mtime +7`; do
	    rm -rfv $f
	done
	cd ..
    done
}

update_setup() {
    for p in x86 x86_64; do
	file=${HOME}/src/grass$1/mswindows/osgeo4w/setup.hint
	pattern=${SRC}/${p}/grass$1/osgeo4w/*[0-9].tar.bz2
    
	curr=`ls -r -w1 $pattern | head -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
	prev=`ls -r -w1 $pattern | head -n2 | tail -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
	version=`grep curr $file | cut -d':' -f2 | cut -d'-' -f1 | tr -d ' '`
    
	sed -e "s/curr:.*/curr: ${version}-$curr/" \
	    -e "s/prev:.*/prev: ${version}-$prev/" $file > \
	    ${SRC}/${p}/grass$1/osgeo4w/setup.hint
    done
}

addons_index() {
    cd $SRC/grass$1/addons
    for d in $(find . -mindepth 1 -maxdepth 1 -type d) ; do
	cd $d/logs
	if [ -f "summary.html" ] ; then
	    ln -sf summary.html index.html
	fi
	cd ../..
    done

    if [ "$1" = "70" ] ; then
        # create symlink to latest version
        cd $SRC/grass$1/addons
	rm latest
	last_version=`ls -w1 | sort -r | head -n2 | tail -n1`
	ln -sf $last_version latest
    fi
}

report() {
    VERSION=$1
    for p in x86 x86_64; do
	cd ${SRC}/${p}/grass${VERSION}/logs
	last_log=`ls -t -w1 . | head -n1`
	if [ -d $last_log ] ; then
	    cat $last_log/error.log 1>&2
	fi
    done
}

download_unzip() {
    wget -q http://147.32.131.91/wingrass/wingrass-${1}.zip
    unzip -o -q wingrass-${1}.zip
    rm wingrass-${1}.zip
}

# geo103 (win) -> geo101
cd $WWW/wingrass
download_unzip x86
download_unzip x86_64

# summary.html -> index.html
### addons_index 64
addons_index 70
addons_index 71

# remove old packages
### rm_7 64
rm_7 70
rm_7 71

# update setup.ini
### update_setup 64
### update_setup 70
update_setup 71

# geo101 -> upload.osgeo.org
### rsync_grass 64
### rsync_grass 70
rsync_grass 71 -daily

# promote changes
~/cronjobs/osgeo4w-promote.sh

### report 64
report 70
report 71

exit 0
