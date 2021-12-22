#!/bin/sh

#
# This script copies built addons manual pages from the winGRASS build server
# To be run on publishing server (grasslxd server)
#
# original author: Martin Landa
# updated for new CMS path MN 8/2015
# updated for grasslxd server MN 6/2020
set -e

if [ $# -ne 1 ] ; then
   echo "To be called from ./cron_grass78_releasebranch_78_build_bins.sh"
   echo "Usage:
   $0 TARGETDIR
   e.g.
   $0 ~/var/www/grass/grass-cms/addons
"
   exit 1
fi

URL=http://geo102.fsv.cvut.cz/grass/addons/
ADDONS=${HOME}/src/grass-addons
#TARGETDIR=/var/www/grass/grass-cms/addons
TARGETDIR=$1

process () {
    major=$1
    minor=$2

    # echo "Updating manuals for GRASS ${major}.${minor}..."
    wget -q $URL/grass${major}/modules.xml -O $TARGETDIR/grass${major}/modules.xml.new
    if [ $? -eq 0 ] ; then
     # don't ruin modules.xml on the Web server if build server is down or broken
     mv -f $TARGETDIR/grass${major}/modules.xml.new $TARGETDIR/grass${major}/modules.xml
    fi
}

process 7 8

exit 0

