#!/bin/bash

DST=/var/www/grass
DIST=dist.x86_64-unknown-linux-gnu
SRC=${HOME}/src/

# check previous build
### ls -lh ${HOME}/.grass*/addons/modules.xml

run=`ps aux | grep "${HOME}/cronjobs/grass-addons.sh c" | wc -l`
if [ "$run" == "2" ]; then
    echo "stopped"
    exit 0
fi

${HOME}/cronjobs/grass-addons.sh

manuals() {
    HTMLDIR=addons
    mkdir $HTMLDIR
    for dir in `find . -maxdepth 1 -type d`; do
        if [ -d $dir/docs/html ] ; then
            cp -r $dir/docs/html/* $HTMLDIR/ 2>/dev/null
        fi
    done
    cp ${SRC}/grass${1}${2}_release/${DIST}/docs/html/grassdocs.css $HTMLDIR/
    cp ${SRC}/grass${1}${2}_release/${DIST}/docs/html/grass_logo.png $HTMLDIR/
    tar czf html.tar.gz $HTMLDIR
    rm -rf $HTMLDIR
}

promote() {
    version=$1
    cd /tmp/.grass${version}/addons
    tar czf logs.tar.gz logs
    manuals $version $2
    cp logs.tar.gz ${DST}/addons/grass${version}
    cp modules.xml ${DST}/addons/grass${version}
    cp html.tar.gz ${DST}/addons/grass${version}
}

promote 6 4
promote 7 0

exit 0
