#!/bin/sh

WWW=/var/www
SRC=/var/www/wingrass
DST=/osgeo/download/osgeo4w

rsync_grass() {
    for p in x86 x86_64; do
	rsync -avg --delete --delete-excluded \
	    ${SRC}/grass${1}/${p}/osgeo4w/ \
	    martinl@upload.osgeo.org:$DST/${p}/release/grass/grass$2
    done
}

rm_7() {
    for p in x86 x86_64; do
	for f in `find $SRC/grass$1/${p}/WinGRASS* -mtime +7`; do
	    rm -rfv $f
	done
	for f in `find $SRC/grass$1/${p}/osgeo4w/grass*.tar.bz2 -mtime +7`; do
	    rm -rfv $f
	done
    done
}

update_setup() {
    for p in x86 x86_64; do
	(cd ${HOME}/src/grass$1 && svn up && cd mswindows/osgeo4w && make)
	file=${HOME}/src/grass$1/mswindows/osgeo4w/setup_${p}.hint
	pattern=${SRC}/grass$1/${p}/osgeo4w/*[0-9].tar.bz2
    
	curr=`ls -r -w1 $pattern | head -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
	prev=`ls -r -w1 $pattern | head -n2 | tail -n1 | cut -d'-' -f4,5 | cut -d'.' -f1`
	version=`grep curr $file | cut -d':' -f2 | cut -d'-' -f1 | tr -d ' '`
    
	sed -e "s/curr:.*/curr: ${version}-$curr/" \
	    -e "s/prev:.*/prev: ${version}-$prev/" $file > \
	    ${SRC}/grass$1/${p}/osgeo4w/setup.hint
    done
}

addons_index() {
    cd ${SRC}/grass$1
    for p in x86 x86_64; do
	cd ${p}/addons
	for d in $(find . -mindepth 1 -maxdepth 1 -type d) ; do
	    cd $d/logs
	    if [ -f "summary.html" ] ; then
		ln -sf summary.html index.html
	    fi
	    cd ../..
	done

	if [ "$1" = "70" ] || [ "$1" = "72" ] ; then
        # create symlink to latest version
            cd ${SRC}/grass$1/${p}/addons
	    rm latest

	    # remove RC builds when release is available
	    for rc in `ls -d grass-*RC[0-9]`; do
		file=`echo $rc | sed 's/RC[0-9]//g'`
		if [ -d $file ] ; then
		    echo "Removing $rc..."
		    rm -rf $rc
		fi
	    done

	    latest_version=`ls -w1 | sort -r | head -n2 | tail -n1`
	    echo "Latest version (grass-${1}/${p}): $latest_version"
	    ln -sf $latest_version latest
	fi
	cd ../..
    done
}

report() {
    VERSION=$1
    cd ${SRC}/grass${VERSION}
    for p in x86 x86_64; do
	cd ${p}/logs
	last_log=`ls -t -w1 . | head -n1`
	if [ -d $last_log ] ; then
	    cat $last_log/error.log 1>&2
	fi
	cd ../..
    done
}

download_unzip() {
    wget -q http://147.32.131.147/wingrass/wingrass.zip
    unzip -o -q wingrass.zip
    rm wingrass.zip
}

# geo103 (win) -> geo101
cd $WWW/wingrass
download_unzip

# summary.html -> index.html
### addons_index 64
addons_index 70
addons_index 72
addons_index 73

# remove old packages
### rm_7 64
rm_7 70
rm_7 72
rm_7 73

# update setup.ini
### update_setup 64
### update_setup 70
update_setup 73

# geo101 -> upload.osgeo.org
### rsync_grass 64
### rsync_grass 70
rsync_grass 73 -daily

# promote changes
~/cronjobs/osgeo4w-promote.sh

### report 64
report 70
report 72
report 73

exit 0
