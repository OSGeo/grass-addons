#!/bin/sh
set -e

#
# Usage:
#
# svn-image.sh image.png
#
# See: https://trac.osgeo.org/grass/wiki/Submitting/Docs#Images
#
# Author: Martin Landa <landa.martin gmail.com>
#

if test -z "$1" ; then
    echo "$0 file.png"
    exit 1
fi

filename=$1
ext="${filename##*.}"
if [ "$ext" != "png" ] ; then
    echo "Only PNG files are supported"
    exit 1
fi
basename=${filename%%.png}

# optionally, but usually worth it (careful color quantization):
pngnq -n 128 -s 3 $filename

# shuffle original and quantitized image names
mv $filename ${basename}_ORIG.png
mv ${basename}-nq8.png $filename

# compress better (lossless)
optipng -o5 ${filename}

exit 0
