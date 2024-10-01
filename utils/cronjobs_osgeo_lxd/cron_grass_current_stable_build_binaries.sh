#!/bin/sh

# script to build GRASS GIS new current binaries + addons + progman from the `releasebranch_8_4` branch
# (c) 2002-2024, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
###################################################################
# how it works:
# - it updates locally the GRASS source code from github server
# - configures source code and then compiles it
# - packages the binaries
# - generated the install scripts
# - generates the pyGRASS 8 HTML manual
# - generates the user 8 HTML manuals
# - injects DuckDuckGo search field

# Preparations, on server (neteler@grasslxd:$):
# - Install PROJ incl Datum shift grids
# - Install GDAL
# - Install apt-get install texlive-latex-extra python3-sphinxcontrib.apidoc
# - install further dependencies:
#     cd $HOME/src/releasebranch_8_4/ && git pull && sudo apt install $(cat .github/workflows/apt.txt)
# - run this script
# - one time only: cross-link code into web space on grasslxd server:
#     cd /var/www/html/
#     ln -s /var/www/code_and_data/grass84 .
#
#################################
# variables for build environment (grass.osgeo.org specific)
USER=`id -u -n`
MAINDIR=/home/$USER
PATH=$MAINDIR/bin:/bin:/usr/bin:/usr/local/bin

# https://github.com/OSGeo/grass/tags
GMAJOR=8
GMINOR=4
GPATCH="0dev"  # required by grass-addons-index.sh
BRANCH=releasebranch_${GMAJOR}_${GMINOR}
DOTVERSION=$GMAJOR.$GMINOR
VERSION=$GMAJOR$GMINOR
GVERSION=$GMAJOR

# fail early
set -e

# compiler optimization
CFLAGSSTRING='-O2'
CFLAGSSTRING='-Werror-implicit-function-declaration -fno-common'
LDFLAGSSTRING='-s'

# define GRASS GIS build related paths:
# where to find the GRASS sources (git clone):
SOURCE=$MAINDIR/src/
GRASSBUILDDIR=$SOURCE/$BRANCH
TARGETMAIN=/var/www/code_and_data
TARGETDIR=$TARGETMAIN/grass${VERSION}/binary/linux/snapshot
TARGETHTMLDIR=$TARGETMAIN/grass${VERSION}/manuals/

# progman not built for older dev versions or old stable, only for preview version
#TARGETPROGMAN=$TARGETMAIN/programming${GVERSION}

MYBIN=$MAINDIR/binaries

############################## nothing to change below:

MYMAKE="nice make -j2 LD_LIBRARY_PATH=$MYBIN/lib:/usr/lib:/usr/local/lib"

# catch CTRL-C and other breaks:
trap "echo 'user break.' ; exit" 2 3 9 15

halt_on_error()
{
  echo "ERROR: $1"
  exit 1
}

# function to configure for compilation
configure_grass()
{
# be sure the targetdir exists
mkdir -p $TARGETDIR

# be sure to be on the right branch
cd $SOURCE/$BRANCH/
git checkout $BRANCH

# cleanup from previous run
rm -f config_$GMAJOR.$GMINOR.git_log.txt

# reset i18N POT files to git, just to be sure
git checkout locale/templates/*.pot

# configure for compilation
CFLAGS=$CFLAGSSTRING LDFLAGS=$LDFLAGSSTRING ./configure \
  --with-cxx \
  --with-sqlite \
  --with-postgres \
  --with-geos \
  --with-odbc \
  --with-cairo --with-cairo-ldflags=-lfontconfig \
  --with-proj-share=/usr/share/proj \
  --with-postgres --with-postgres-includes=/usr/include/postgresql \
  --with-freetype --with-freetype-includes=/usr/include/freetype2 \
  --with-netcdf \
  --with-pdal \
  --with-fftw \
  --with-nls \
  --with-libsvm \
  --with-blas \
  --with-lapack \
  --with-zstd \
  2>&1 | tee config_$DOTVERSION.git_log.txt

 if [ $? -ne 0 ] ; then
   halt_on_error "configure doesn't work."
 fi
}

# be sure the directories are there

mkdir -p $TARGETDIR
cd $GRASSBUILDDIR/

# clean up from previous run
touch include/Make/Platform.make
$MYMAKE distclean > /dev/null 2>&1

# cleanup leftover garbage
git status | grep '.rst' | xargs rm -f
rm -rf lib/python/docs/_build/ lib/python/docs/_templates/layout.html
rm -f config_${DOTVERSION}.git_log.txt ChangeLog

# be sure to be on the right branch
git checkout $BRANCH

echo "git update..."
git fetch --all --prune && git checkout $BRANCH && git pull --rebase || halt_on_error "git update error!"
git status

# for the "contributors list" in old CMSMS (still needed for hugo?)
mkdir -p $TARGETMAIN/uploads/grass/
cp -f *.csv $TARGETMAIN/uploads/grass/

# configure for compilation
echo "configuring"
configure_grass || (echo "$0: an error occurred" ; exit 1)
pwd
ARCH=`cat include/Make/Platform.make | grep ^ARCH | cut -d'=' -f2 | xargs`

########  now GRASS GIS source code is prepared ####################
#### next compile GRASS, takes a while
$MYMAKE


echo "GRASS $VERSION compilation done"

########  now GRASS GIS binaries are prepared ####################

#### create module overview (https://trac.osgeo.org/grass/ticket/1203)
#sh utils/module_synopsis.sh

#### generate developer stuff: pygrass docs + gunittest docs
# generate pyGRASS sphinx manual (in docs/html/libpython/)
# including source code
$MYMAKE sphinxdoclib

##
echo "Copy over the manual + pygrass HTML pages:"
mkdir -p $TARGETHTMLDIR
mkdir -p $TARGETHTMLDIR/addons # indeed only relevant the very first compile time
# don't destroy the addons during update
\mv $TARGETHTMLDIR/addons /tmp
rm -f $TARGETHTMLDIR/*.*
(cd $TARGETHTMLDIR ; rm -rf barscales colortables icons northarrows)
\mv /tmp/addons $TARGETHTMLDIR

cp -rp dist.$ARCH/docs/html/* $TARGETHTMLDIR/
echo "Copied pygrass progman to http://grass.osgeo.org/grass${VERSION}/manuals/libpython/"

# search to be improved with mkdocs or similar; for now we use DuckDuckGo
echo "Injecting DuckDuckGo search field into manual main page..."
(cd $TARGETHTMLDIR/ ; sed -i -e "s+</table>+</table><\!\-\- injected in cron_grass8_relbranch_build_binaries.sh \-\-> <center><iframe src=\"https://duckduckgo.com/search.html?site=grass.osgeo.org%26prefill=Search%20manual%20pages%20at%20DuckDuckGo\" style=\"overflow:hidden;margin:0;padding:0;width:410px;height:40px;\" frameborder=\"0\"></iframe></center>+g" index.html)

# copy important files to web space
cp -p AUTHORS CITING CITATION.cff COPYING GPL.TXT INSTALL.md REQUIREMENTS.md $TARGETDIR/

# clean wxGUI sphinx manual etc
(cd $GRASSBUILDDIR/ ; $MYMAKE cleansphinx)

############
# generate doxygen programmers's G8 manual
cd $GRASSBUILDDIR/
#$MYMAKE htmldocs-single > /dev/null || (echo "$0 htmldocs-single: an error occurred" ; exit 1)
$MYMAKE htmldocs-single || (echo "$0 htmldocs-single: an error occurred" ; exit 1)

cd $GRASSBUILDDIR/

#### unused, only done in "preview" script
## clean old TARGETPROGMAN stuff from last run
#if  [ -z "$TARGETPROGMAN" ] ; then
# echo "\$TARGETPROGMAN undefined, error!"
# exit 1
#fi
#mkdir -p $TARGETPROGMAN
#rm -f $TARGETPROGMAN/*.*
#
## copy over doxygen manual
#cp -r html/*  $TARGETPROGMAN/
#
#echo "Copied HTML progman to https://grass.osgeo.org/programming${GVERSION}"
## fix permissions
#chgrp -R grass $TARGETPROGMAN/*
#chmod -R a+r,g+w $TARGETPROGMAN/
#chmod -R a+r,g+w $TARGETPROGMAN/*
## bug in doxygen
#(cd $TARGETPROGMAN/ ; ln -s index.html main.html)
#### end unused

##### generate i18N stats for HTML page path:
# note: the gettext POT files are managed in git and OSGeo Weblate
## Structure:  grasslibs_ar.po 144 translated messages 326 fuzzy translations 463 untranslated messages.
cd $GRASSBUILDDIR
(cd locale/ ;
touch po/*.po ;
$MYMAKE mo > out.i18n 2>&1 ;
# libs, mods, wx
# hack:
cat out.i18n | tr '\n' ' ' | sed -e 's+ msgfmt+\
msgfmt+g' | tr -s ' ' ' ' | cut -d' ' -f5,6- | sed 's+\,++g' | sed 's+^po/++g' | grep -v 'done for' | sort > $TARGETDIR/i18n_stats.txt
rm -f out.i18n
)

cd $TARGETDIR/
cat i18n_stats.txt | grep mod  > i18n_stats_mods.txt
cat i18n_stats.txt | grep lib  > i18n_stats_libs.txt
cat i18n_stats.txt | grep wxpy > i18n_stats_wxpy.txt
cd $GRASSBUILDDIR

# package the GRASS GIS package
$MYMAKE bindist
if [ $? -ne 0 ] ; then
   halt_on_error "make bindist."
fi

# report system:
echo "System:
$ARCH, compiled with:" > grass-$DOTVERSION\_$ARCH\_bin.txt
## echo "Including precompiled $GDALVERSION library for r.in.gdal" >> grass-$DOTVERSION\_$ARCH\_bin.txt
gcc -v 2>&1 | grep -v Reading >> grass-$DOTVERSION\_$ARCH\_bin.txt

# clean old version from previous run
rm -f $TARGETDIR/grass-$DOTVERSION\_$ARCH\_bin.txt
rm -f $TARGETDIR/grass-${DOTVERSION}*.tar.gz
rm -f $TARGETDIR/grass-${DOTVERSION}*install.sh

############################################
echo "Copy new binary version into web space:"
cp -p grass-$DOTVERSION\_$ARCH\_bin.txt grass-${DOTVERSION}*.tar.gz grass-${DOTVERSION}*install.sh $TARGETDIR
rm -f grass-$DOTVERSION\_$ARCH\_bin.txt grass-${DOTVERSION}*.tar.gz grass-${DOTVERSION}*install.sh

# generate manual ZIP package
(cd $TARGETHTMLDIR/.. ; rm -f $TARGETHTMLDIR/*html_manual.zip ; zip -r /tmp/grass-${DOTVERSION}_html_manual.zip manuals/)
mv /tmp/grass-${DOTVERSION}_html_manual.zip $TARGETHTMLDIR/

# error log etc
cp -f config_$DOTVERSION.git_log.txt $TARGETDIR
cp -f error.log $TARGETDIR
chmod -R a+r,g+w $TARGETDIR     2> /dev/null
chmod -R a+r,g+w $TARGETHTMLDIR 2> /dev/null

echo "Written to: $TARGETDIR"

cd $GRASSBUILDDIR

############################################
# compile addons

# update addon repo (addon repo has been cloned twice on the server to
# have separate grass7 and grass8 addon compilation)
# fetch addon repo if needed
cd "$SOURCE/"
# Check if the addon repository is already cloned
if [ -d "grass${GMAJOR}-addons" ]; then
  echo "The GRASS GIS repository <grass${GMAJOR}-addons> has already been cloned. Continuing..."
else
  echo "Cloning the GRASS GIS repository <grass${GMAJOR}-addons> first..."
  git clone https://github.com/OSGeo/grass-addons.git grass${GMAJOR}-addons
  if [ $? -eq 0 ]; then
    echo "Repository successfully cloned."
  else
    echo "Error: Failed to clone the repository."
    exit 1
  fi
fi
# setup source code repo
(cd $SOURCE/grass$GMAJOR-addons/; git checkout grass$GMAJOR; git pull origin grass$GMAJOR)
# compile addons
cd $GRASSBUILDDIR
sh $MAINDIR/cronjobs/compile_addons_git.sh $GMAJOR \
   $GMINOR \
   $SOURCE/grass$GMAJOR-addons/src/ \
   $SOURCE/$BRANCH/dist.$ARCH/ \
   $MAINDIR/.grass$GMAJOR/addons \
   $SOURCE/$BRANCH/bin.$ARCH/grass \
   1
mkdir -p $TARGETHTMLDIR/addons/
# copy individual addon html files into one target dir if compiled addon
# has own dir e.g. $MAINDIR/.grass8/addons/db.join/ with bin/ docs/ etc/ scripts/
# subdir
for dir in `find $MAINDIR/.grass$GMAJOR/addons -maxdepth 1 -type d`; do
    if [ -d $dir/docs/html ] ; then
        if [ "$(ls -A $dir/docs/html/)" ]; then
            for f in $dir/docs/html/*; do
                cp $f $TARGETHTMLDIR/addons/
            done
        fi
    fi
done
sh $MAINDIR/cronjobs/grass-addons-index.sh $GMAJOR $GMINOR $GPATCH $TARGETHTMLDIR/addons/
# copy over hamburger menu assets
cp $TARGETHTMLDIR/grass_logo.png \
   $TARGETHTMLDIR/hamburger_menu.svg \
   $TARGETHTMLDIR/hamburger_menu_close.svg \
   $TARGETHTMLDIR/grassdocs.css \
   $TARGETHTMLDIR/addons/
chmod -R a+r,g+w $TARGETHTMLDIR 2> /dev/null

# copy over logs from $MAINDIR/.grass$GMAJOR/addons/logs/
mkdir -p $TARGETMAIN/addons/grass$GMAJOR/logs/
cp -p $MAINDIR/.grass$GMAJOR/addons/logs/* $TARGETMAIN/addons/grass$GMAJOR/logs/

# generate addons modules.xml file (required for g.extension module)
$SOURCE/$BRANCH/bin.$ARCH/grass --tmp-project EPSG:4326 --exec $MAINDIR/cronjobs/build-xml.py --build $MAINDIR/.grass$GMAJOR/addons
cp $MAINDIR/.grass$GMAJOR/addons/modules.xml $TARGETMAIN/addons/grass$GMAJOR/modules.xml

# regenerate keywords.html file with addons modules keywords
export ARCH
export ARCH_DISTDIR=$GRASSBUILDDIR/dist.$ARCH
export GISBASE=$ARCH_DISTDIR
export VERSION_NUMBER=$DOTVERSION
python3 $GRASSBUILDDIR/man/build_keywords.py $TARGETMAIN/grass$GMAJOR$GMINOR/manuals/ $TARGETMAIN/grass$GMAJOR$GMINOR/manuals/addons/
unset ARCH ARCH_DISTDIR GISBASE VERSION_NUMBER

############################################
# create sitemaps to expand the hugo sitemap

python3 $HOME/src/grass$GMAJOR-addons/utils/create_manuals_sitemap.py --dir=/var/www/code_and_data/grass$GMAJOR$GMINOR/manuals/ --url=https://grass.osgeo.org/grass$GMAJOR$GMINOR/manuals/ -o
python3 $HOME/src/grass$GMAJOR-addons/utils/create_manuals_sitemap.py --dir=/var/www/code_and_data/grass$GMAJOR$GMINOR/manuals/addons/ --url=https://grass.osgeo.org/grass$GMAJOR$GMINOR/manuals/addons/ -o

############################################
# cleanup
cd $GRASSBUILDDIR
$MYMAKE distclean  > /dev/null || (echo "$0: an error occurred" ; exit 1)
rm -rf lib/html/ lib/latex/

echo "Finished GRASS $VERSION $ARCH compilation."
echo "Written to: $TARGETDIR"
echo "Copied HTML ${GVERSION} manual to https://grass.osgeo.org/grass${VERSION}/manuals/"
echo "Copied pygrass progman ${GVERSION} to https://grass.osgeo.org/grass${VERSION}/manuals/libpython/"
## echo "Copied HTML ${GVERSION} progman to https://grass.osgeo.org/programming${GVERSION}"
echo "Copied Addons ${GVERSION} to https://grass.osgeo.org/grass${VERSION}/manuals/addons/"

exit 0
