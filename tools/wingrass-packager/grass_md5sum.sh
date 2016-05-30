#!/bin/sh
# Create mdb5sum files for GRASS versions
#
# Options:
#  - platform (32 or 64)
#  - src postfix, eg. '70'

HOME=/c/Users/landa/grass_packager

if test -z "$1"; then
    echo "platform not specified"
    exit 1
fi
PLATFORM=$1
export PATH=/c/msys${PLATFORM}/usr/bin:/c/msys${PLATFORM}/mingw${PLATFORM}/bin:/c/osgeo4w${PLATFORM}/bin:${PATH}

if [ "$PLATFORM" = "32" ] ; then
    PLATFORM_DIR=x86
else
    PLATFORM_DIR=x86_64
fi

function create_md5sum {
    GRASS_DIR=$1
    
    cd ${HOME}/${GRASS_DIR}/${PLATFORM_DIR}
    for file in `ls WinGRASS*.exe`; do
	md5sum $file > ${file}.md5sum
    done
}

if test -z $2 ; then
    # dev packages
    ### create_md5sum grass64
    create_md5sum grass70
    create_md5sum grass72
    create_md5sum grass73
else
    create_md5sum grass$2
fi

exit 0
