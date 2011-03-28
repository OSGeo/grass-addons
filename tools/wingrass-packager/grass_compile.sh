#!/bin/sh
# Compile GRASS 6.4, 6.5 and 7.0 (update source code from SVN repository)

SRC=/osgeo4w/usr/src

function update {
    echo "Updating $1..."     
    cd $SRC/$1
    svn up || (svn cleanup && svn up)
}

function update_wxgui_psmap {
    psmap_dir="$SRC/grass_addons/gui/wxpython/wx.psmap"
    cd $SRC/$1/gui
    cp $psmap_dir/docs/*.html      wxpython/docs/
    cp $psmap_dir/gui_modules/*.py wxpython/gui_modules/
    cp $psmap_dir/images/*.png     images/
    cp $psmap_dir/xml/*.xml        wxpython/xml/
}

function compile {
    echo "Compiling $1..."
    cd $SRC/$1
    rm -f mswindows/osgeo4w/configure-stamp
    svn up || (svn cleanup && svn up)
    ./mswindows/osgeo4w/package.sh
}

export PATH=$PATH:/c/OSGeo4W/apps/msys/bin

update grass_addons

update_wxgui_psmap grass64_release
update_wxgui_psmap grass6_devel
update_wxgui_psmap grass_trunk

compile grass64_release
compile grass6_devel
compile grass_trunk

exit 0
