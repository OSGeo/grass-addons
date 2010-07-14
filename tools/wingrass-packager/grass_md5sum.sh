#!/bin/sh
# Create mdb5sum files for GRASS 6.4, 6.5 and 7.0

HOME=/c/Users/landa/grass_packager

function create_md5sum {
    cd $HOME/$1
    for file in `ls WinGRASS*.exe`; do
	md5sum $file > ${file}.md5sum
    done
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

create_md5sum grass64
create_md5sum grass65
create_md5sum grass70

exit 0
