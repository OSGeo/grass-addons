#!/bin/sh

# Update wiki installation (git pull)

IKIPATH=/osgeo/grass/grass-wiki
VERSION=1_20

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
