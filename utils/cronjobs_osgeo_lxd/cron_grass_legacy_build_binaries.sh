#!/bin/sh

# script to build GRASS GIS legacy binaries + addons from the `releasebranch_7_8` branch
# (c) 2008-2024, GPL 2+ Markus Neteler <neteler@osgeo.org>
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
###################################################################
# how it works:
# - it updates locally the GRASS source code from github server
# - configures, compiles
# - packages the binaries
# - generated the install scripts
# - generates the pyGRASS 7 HTML manual
# - generates the user 7 HTML manuals
# - injects DuckDuckGo search field
# - injects "G8.x is the new version" box into core and addon manual pages
# - injects canonical URL

# Preparations, on server (neteler@grasslxd:$):
#  - Install PROJ
#  - Install GDAL
#  - Install apt-get install texlive-latex-extra python3-sphinxcontrib.apidoc
#  - Clone source from github:
#    mkdir -p ~/src ; cd ~/src
#    git clone https://github.com/OSGeo/grass.git releasebranch_7_8
#    cd releasebranch_7_8
#    git checkout releasebranch_7_8
#  - Prepare target directories:
#    cd /var/www/code_and_data/
#    mkdir grass78
#    cd /var/www/html/
#    ln -s /var/www/code_and_data/grass78 .
#
#################################
# variables for build environment (grass.osgeo.org specific)
MAINDIR=/home/neteler
PATH=$MAINDIR/bin:/bin:/usr/bin:/usr/local/bin

# https://github.com/OSGeo/grass/tags
GMAJOR=7
GMINOR=8
GPATCH=7 # required by grass-addons-index.sh

# NEW_CURRENT: set to same value as in cron_grass_old_build_binaries.sh
NEW_CURRENT=84

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
BRANCH=releasebranch_${GMAJOR}_$GMINOR
GRASSBUILDDIR=$SOURCE/$BRANCH
TARGETMAIN=/var/www/code_and_data
TARGETDIR=$TARGETMAIN/grass${VERSION}/binary/linux/snapshot
TARGETHTMLDIR=$TARGETMAIN/grass${VERSION}/manuals/

# progman not built for older dev versions or old stable, only for preview
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
  --with-blas --with-blas-includes=/usr/include/atlas/ \
  --with-lapack --with-lapack-includes=/usr/include/atlas/ \
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
(cd $TARGETHTMLDIR/ ; sed -i -e "s+</table>+</table><\!\-\- injected in cron_grass7_relbranch_build_binaries.sh \-\-> <center><iframe src=\"https://duckduckgo.com/search.html?site=grass.osgeo.org%26prefill=Search%20manual%20pages%20at%20DuckDuckGo\" style=\"overflow:hidden;margin:0;padding:0;width:410px;height:40px;\" frameborder=\"0\"></iframe></center>+g" index.html)

# copy important files to web space
cp -p AUTHORS CHANGES CITING COPYING GPL.TXT INSTALL REQUIREMENTS.html $TARGETDIR/

# clean wxGUI sphinx manual etc
(cd $GRASSBUILDDIR/ ; $MYMAKE cleansphinx)

############
# generate doxygen programmers's G8 manual
## -> no, only in GRASS GIS 8 versions

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
(cd ~/src/grass$GMAJOR-addons/; git checkout grass$GMAJOR; git pull origin grass$GMAJOR)
# compile addons
cd $GRASSBUILDDIR
sh ~/cronjobs/compile_addons_git.sh $GMAJOR \
   $GMINOR \
   ~/src/grass$GMAJOR-addons/src/ \
   ~/src/$BRANCH/dist.$ARCH/ \
   ~/.grass$GMAJOR/addons \
   ~/src/$BRANCH/bin.$ARCH/grass$VERSION \
   1
mkdir -p $TARGETHTMLDIR/addons/
# copy individual addon html files into one target dir if compiled addon
# has own dir e.g. ~/.grass7/addons/db.join/ with bin/ docs/ etc/ scripts/
# subdir
for dir in `find ~/.grass$GMAJOR/addons -maxdepth 1 -type d`; do
    if [ -d $dir/docs/html ] ; then
        if [ "$(ls -A $dir/docs/html/)" ]; then
            for f in $dir/docs/html/*; do
                cp $f $TARGETHTMLDIR/addons/
            done
        fi
    fi
done
sh ~/cronjobs/grass-addons-index.sh $GMAJOR $GMINOR $GPATCH $TARGETHTMLDIR/addons/
chmod -R a+r,g+w $TARGETHTMLDIR 2> /dev/null

# copy over logs from ~/.grass$GMAJOR/addons/logs/
mkdir -p $TARGETMAIN/addons/grass$GMAJOR/logs/
cp -p ~/.grass$GMAJOR/addons/logs/* $TARGETMAIN/addons/grass$GMAJOR/logs/

# generate addons modules.xml file (required for g.extension module)
~/src/$BRANCH/bin.$ARCH/grass$VERSION --tmp-location EPSG:4326 --exec ~/cronjobs/build-xml.py --build ~/.grass$GMAJOR/addons
cp ~/.grass$GMAJOR/addons/modules.xml $TARGETMAIN/addons/grass$GMAJOR/modules.xml

# regenerate keywords.html file with addons modules keywords
export ARCH
export ARCH_DISTDIR=$GRASSBUILDDIR/dist.$ARCH
export GISBASE=$ARCH_DISTDIR
export VERSION_NUMBER=$DOTVERSION
python3 $GRASSBUILDDIR/man/build_keywords.py $TARGETHTMLDIR/ $TARGETHTMLDIR/addons/
unset ARCH ARCH_DISTDIR GISBASE VERSION_NUMBER

############################################
# Inject hint to new current version hint in a red box into each manual page
# for core manual pages
echo "Injecting G8.x new current version hint in a red box into MAN pages..."
# inject G8.x current stable version hint in a red box:
(cd $TARGETHTMLDIR/ ; for myfile in `grep -L 'document is for an older version of GRASS GIS' *.html` ; do sed -i -e "s:<div id=\"container\">:<div id=\"container\"><p style=\"border\:3px; border-style\:solid; border-color\:#BC1818; padding\: 1em;\">Note\: This document is for an older version of GRASS GIS that will be discontinued soon. You should upgrade, and read the <a href=\"../../../grass${NEW_CURRENT}/manuals/$myfile\">current manual page</a>.</p>:g" $myfile ; done)
# also for addons, separately for landing page and addons
(cd $TARGETHTMLDIR/addons/ ; sed -i -e "s:<table><tr><td>:<hr class=\"header\"><p style=\"border\:3px; border-style\:solid; border-color\:#BC1818; padding\: 1em;\">Note\: This document is for an older version of GRASS GIS that will be discontinued soon. You should upgrade, and read the <a href=\"../../../grass${NEW_CURRENT}/manuals/addons/index.html\">current addon manual page</a>.</p> <table><tr><td>:g" index.html)
(cd $TARGETHTMLDIR/addons/ ; for myfile in `grep -L 'document is for an older version of GRASS GIS' *.html` ; do sed -i -e "s:<div id=\"container\">:<div id=\"container\"><p style=\"border\:3px; border-style\:solid; border-color\:#BC1818; padding\: 1em;\">Note\: This document is for an older version of GRASS GIS that will be discontinued soon. You should upgrade, and read the <a href=\"../../../grass${NEW_CURRENT}/manuals/addons/$myfile\">current manual page</a>.</p>:g" $myfile ; done)
# also for Python
(cd $TARGETHTMLDIR/libpython/ ; for myfile in `grep -L 'document is for an older version of GRASS GIS' *.html` ; do sed -i -e "s:^<hr class=\"header\">:<hr class=\"header\"><p style=\"border\:3px; border-style\:solid; border-color\:#BC1818; padding\: 1em;\">Note\: This document is for an older version of GRASS GIS that will be discontinued soon. You should upgrade, and read the <a href=\"../../../../grass${NEW_CURRENT}/manuals/libpython/$myfile\">current Python manual page</a>.</p>:g" $myfile ; done)

# SEO: inject canonical link into all (old) manual pages to point to latest stable (avoid "duplicate content" SEO punishment)
# see https://developers.google.com/search/docs/crawling-indexing/consolidate-duplicate-urls
# canonical: once again after addon manual (re)creation, only where missing
(cd $TARGETHTMLDIR/ ; for myfile in `grep -L 'link rel="canonical"' *.html` ; do sed -i -e "s:</head>:<link rel=\"canonical\" href=\"https\://grass.osgeo.org/grass${NEW_CURRENT}/manuals/$myfile\">\n</head>:g" $myfile ; done)
(cd $TARGETHTMLDIR/addons/ ; for myfile in `grep -L 'link rel="canonical"' *.html` ; do sed -i -e "s:</head>:<link rel=\"canonical\" href=\"https\://grass.osgeo.org/grass${NEW_CURRENT}/manuals/addons/$myfile\">\n</head>:g" $myfile ; done)
(cd $TARGETHTMLDIR/libpython/ ; for myfile in `grep -L 'link rel="canonical"' *.html` ; do sed -i -e "s:</head>:<link rel=\"canonical\" href=\"https\://grass.osgeo.org/grass${NEW_CURRENT}/manuals/libpython/$myfile\">\n</head>:g" $myfile ; done)


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
echo "Copied Addons ${GVERSION} to https://grass.osgeo.org/grass${VERSION}/manuals/addons/"

exit 0
