#!/bin/sh

# Update wiki installation (git pull)

WIKIPATH=/osgeo/grass/grass-wiki
if test -z "$1" ; then
    VERSION=1_20
else
    VERSION=$1
fi

cd $WIKIPATH
git branch | grep REL$VERSION | grep '^*'
if [ "$?" -ne 0 ] ; then
    git checkout -b REL$VERSION origin/REL$VERSION
fi
git pull

cd $WIKIPATH/extensions
for ext in `ls -l | grep ^d | awk '{print $9}'` ; do
    echo $ext...
    cd $ext
    git pull
    cd ..
done

exit 0
