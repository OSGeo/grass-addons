#!/bin/bash
## Converts an html file generated from markdown into
## the format expected for GRASS documentation.
## Specifcally, html tags are converted to expected
## ones, and unacceptable tags are removed. Lines are
## then wrapped at 80 chars.
if [ "$1" == "-h" ] ||  [ $# -eq 0 ] ; then
    echo "Converts an html file generated from markdown
into the format expected for GRASS documentation."
    echo "Usage: `basename $0` inputfile.html [-h]"
    exit 0
fi
tf=$!"tmp.txt"
sed -r -i 's|<head>.*</head>||g' $1
sed -r -i 's|<(/)?html>||g' $1
sed -r -i 's|<(/)?body>||g' $1
sed -r 's|<(/)?strong>|<\1b>|g' $1 >$tf
fmt -w 80 $tf >$1
rm -f $tf
