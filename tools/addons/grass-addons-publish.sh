#!/bin/sh

# This script copies built addons manual pages from the build server
# and creates index page
#
# To be run on publishing server (see crontab.publish)
#
# original author: Martin Landa
# updated for new CMS path MN 8/2015
set -e

URL=http://geo102.fsv.cvut.cz/grass/addons/
ADDONS=${HOME}/src/grass-addons

process () {
    major=$1
    minor=$2

    # echo "Updating manuals for GRASS ${major}.${minor}..."
    wget -q $URL/grass${major}/modules.xml -O /var/www/grass/grass-cms/addons/grass${major}/modules.xml.new
    if [ $? -eq 0 ] ; then
     # don't ruin modules.xml on the Web server if build server is down or broken
     mv -f /var/www/grass/grass-cms/addons/grass${major}/modules.xml.new /var/www/grass/grass-cms/addons/grass${major}/modules.xml
    fi
    wget -q $URL/grass${major}/logs.tar.gz -O logs.tar.gz
    wget -q $URL/grass${major}/html.tar.gz -O html.tar.gz

    tar xzf logs.tar.gz
    rm -rf /var/www/grass/grass-cms/addons/grass${major}/logs
    mv logs /var/www/grass/grass-cms/addons/grass${major}/

    tar xzf html.tar.gz
    rm -rf /var/www/grass/grass-cms/grass${major}${minor}/manuals/addons
    mv addons /var/www/grass/grass-cms/grass${major}${minor}/manuals/
    chgrp -R grass /var/www/grass/grass-cms/grass${major}${minor}/manuals/addons
    chmod -R g+w   /var/www/grass/grass-cms/grass${major}${minor}/manuals/addons
    rm logs.tar.gz
    rm html.tar.gz
}

cd $ADDONS
nup=`git pull | wc -l`
if [ "$nup" -gt 1 ] || [ "$1" = "f" ] ; then
    process 7 8
    process 6 4 

    ${ADDONS}/tools/addons/grass-addons-index.sh
fi

exit 0
