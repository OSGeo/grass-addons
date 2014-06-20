#!/bin/sh

#
# Usage:
#
# merge from trunk
# svn-merge.sh 60867
#
# merge from specified branch
# svn-merge.sh 60867 releasebranch_6_4
#
# Author: Martin Landa <landa.martin gmail.com>
#

if test -z "$1" ; then
    echo "$0 rev"
    exit 1
fi
if test -z "$2" ; then
    SVN_BRANCH=https://svn.osgeo.org/grass/grass/trunk
else
    SVN_BRANCH=https://svn.osgeo.org/grass/grass/branches/$2
fi

svn merge -c "$1" $SVN_BRANCH
svn propdel svn:mergeinfo .

exit 0
