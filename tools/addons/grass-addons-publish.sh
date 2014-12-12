#!/bin/sh

URL=http://geo102.fsv.cvut.cz/grass/addons/
ADDONS=${HOME}/src/grass-addons/tools/addons

process () {
    major=$1
    minor=$2
    wget -q $URL/grass${major}/modules.xml -O /osgeo/grass/grass-cms/addons/grass${major}/modules.xml
    wget -q $URL/grass${major}/logs.tar.gz -O logs.tar.gz
    wget -q $URL/grass${major}/html.tar.gz -O html.tar.gz

    tar xzf logs.tar.gz
    rm -rf /osgeo/grass/grass-cms/addons/grass${major}/logs
    mv logs /osgeo/grass/grass-cms/addons/grass${major}/

    tar xzf html.tar.gz
    rm -rf /osgeo/grass/grass-cms/grass${major}${minor}/manuals/addons
    mv addons /osgeo/grass/grass-cms/grass${major}${minor}/manuals/
    rm logs.tar.gz
    rm html.tar.gz
}

process 7 0
process 6 4 

${ADDONS}/grass-addons-index.sh

exit 0
