#!/bin/sh
# Create mdb5sum files for GRASS versions

HOME=/c/Users/landa/grass_packager

function create_md5sum {
    cd $HOME/$1
    for file in `ls WinGRASS*.exe`; do
	md5sum $file > ${file}.md5sum
    done
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

if test -z $1 ; then
    # dev packages
    create_md5sum grass64
    ### create_md5sum grass65
    create_md5sum grass70
    create_md5sum grass71
else
    create_md5sum grass$1
fi

exit 0
