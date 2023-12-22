#!/bin/sh

# script to build GRASS 7.x relbranch74 binaries (shared libs)
# (c) GPL 2+ Markus Neteler <neteler@osgeo.org>
# Sat Mar 29 13:05:53 PDT 2014
# Tue Apr 22 11:23:12 PDT 2014
# Sat Sep 19 03:43:34 PDT 2015
# Wed May 25 10:05:05 PDT 2016
# Sun Nov 12 22:02:53 CET 2017
# Sun 02 Jun 2019 03:30:38 PM CEST
# Sun 27 Oct 2019 09:00:14 PM CET
# Thu 16 Jan 2020 08:17:43 AM UTC
#
# GRASS GIS github, https://github.com/OSGeo/grass
#
## prep, neteler@osgeo6:$
# mkdir -p ~/src
# cd ~/src
# for i in 2 4 6 ; do git clone https://github.com/OSGeo/grass.git releasebranch_7_$i ; done
# for i in 2 4 6 ; do (cd releasebranch_7_$i ;  git checkout releasebranch_7_$i ) ; done
#
###################################################################
# how it works:
# - it updates the GRASS source code from github server
# - configures, compiles
# - packages the binaries
# - generated the install scripts
# - generates the pyGRASS HTML manual
# - generates the user HTML manuals

# Preparations:
#  - Install PROJ: http://trac.osgeo.org/proj/ incl Datum shift grids
#     sh conf_proj4.sh
#  - Install GDAL: http://trac.osgeo.org/gdal/wiki/DownloadSource
#     sh conf_gdal.sh
#  - Install apt-get install texlive-latex-extra sphinx-apidoc
#  - Clone source from github
#################################
PATH=/home/neteler/binaries/bin:/usr/bin:/bin:/usr/X11R6/bin:/usr/local/bin

GMAJOR=7
GMINOR=4
DOTVERSION=$GMAJOR.$GMINOR
VERSION=$GMAJOR$GMINOR
GVERSION=$GMAJOR

###################
CFLAGSSTRING='-O2'
CFLAGSSTRING='-Werror-implicit-function-declaration -fno-common'
LDFLAGSSTRING='-s'

#define several paths if required:

MAINDIR=/home/neteler
# where to find the GRASS sources (git clone):
SOURCE=$MAINDIR/src/
BRANCH=releasebranch_7_$GMINOR
GRASSBUILDDIR=$SOURCE/$BRANCH
TARGETMAIN=/var/www/code_and_data/
TARGETDIR=$TARGETMAIN/grass${VERSION}/binary/linux/snapshot
TARGETHTMLDIR=$TARGETMAIN/grass${VERSION}/manuals/
# programmer's manual is build only from the main branch

MYBIN=$MAINDIR/binaries

############################## nothing to change below:

MYMAKE="nice make LD_LIBRARY_PATH=$MYBIN/lib:/usr/lib:/usr/local/lib"

# catch CTRL-C and other breaks:
trap "echo 'user break.' ; exit" 2 3 9 15

halt_on_error()
{
  echo "ERROR: $1"
  exit 1
}

configure_grass()
{

#  --enable-64bit \
#  --with-libs=/usr/lib64 \

# which package?
#   --with-mysql --with-mysql-includes=/usr/include/mysql --with-mysql-libs=/usr/lib/mysql \


CFLAGS=$CFLAGSSTRING LDFLAGS=$LDFLAGSSTRING ./configure \
  --with-cxx \
  --with-sqlite \
  --with-postgres \
  --with-geos \
  --with-odbc \
  --with-cairo --with-cairo-ldflags=-lfontconfig \
  --with-proj --with-proj-share=/usr/share/proj \
  --with-postgres --with-postgres-includes=/usr/include/postgresql \
  --with-freetype --with-freetype-includes=/usr/include/freetype2 \
  --with-netcdf \
  --with-pdal \
  --with-fftw \
  --with-nls \
  --with-blas --with-blas-includes=/usr/include/atlas/ \
  --with-lapack --with-lapack-includes=/usr/include/atlas/ \
  --with-zstd \
  --without-motif \
  --without-liblas \
  2>&1 | tee config_$DOTVERSION.git_log.txt

 if [ $? -ne 0 ] ; then
   halt_on_error "configure doesn't work."
 fi
}

######## update from git:

mkdir -p $TARGETDIR
cd $GRASSBUILDDIR/

$MYMAKE distclean > /dev/null 2>&1

# cleanup leftover garbage
git status | grep '.rst' | xargs rm -f
rm -rf lib/python/docs/_build/ lib/python/docs/_templates/layout.html
rm -f config_${DOTVERSION}.git_log.txt ChangeLog

# be sure to be on branch
git checkout $BRANCH

echo "git update..."
git fetch --all --prune && git checkout $BRANCH && git pull --rebase || halt_on_error "git update error!"
git status

# for the contributors list in CMS
cp -f *.csv $TARGETMAIN/uploads/grass/

#configure
echo "configuring"
$MYMAKE distclean  > /dev/null
configure_grass || (echo "$0: an error occured" ; exit 1)
pwd
ARCH=`cat config.status |grep '@host@' | cut -d'%' -f3`

########  now GRASS is prepared ####################

#### next compile GRASS:
$MYMAKE


echo "GRASS $VERSION compilation done"

# now GRASS is prepared ############################################

#### create module overview (https://trac.osgeo.org/grass/ticket/1203)
#sh utils/module_synopsis.sh

#### generate developer stuff: pygrass docs + gunittest docs
# generate pyGRASS sphinx manual (in docs/html/libpython/)
# including source code
$MYMAKE sphinxdoclib

##
echo "Copy over the manual + pygrass HTML pages:"
mkdir -p $TARGETHTMLDIR
# don't destroy the addons
\mv $TARGETHTMLDIR/addons /tmp
rm -f $TARGETHTMLDIR/*.*
(cd $TARGETHTMLDIR ; rm -rf barscales colortables icons northarrows)
\mv /tmp/addons $TARGETHTMLDIR

cp -rp dist.$ARCH/docs/html/* $TARGETHTMLDIR/
echo "Copied pygrass progman to http://grass.osgeo.org/grass${VERSION}/manuals/libpython/"

cp -p AUTHORS CHANGES CITING COPYING GPL.TXT INSTALL REQUIREMENTS.html $TARGETDIR/

# inject G7.x new version hint in a red box:
(cd $TARGETHTMLDIR/ ; for myfile in `ls *.html` ; do sed -i -e "s:<hr class=\"header\">:<hr class=\"header\"><p style=\"border\:3px; border-style\:solid; border-color\:#BC1818; padding\: 1em;\">Note\: A new GRASS GIS stable version has been released\: GRASS GIS 7.8, available <a href=\"https\://grass.osgeo.org/download/\">here</a>\.<br> Updated manual page\: <a href=\"../../grass78/manuals/$myfile\">here</a></p>:g" $myfile ; done)
# also for Python
(cd $TARGETHTMLDIR/libpython/ ; for myfile in `ls *.html` ; do sed -i -e "s:<hr class=\"header\">:<hr class=\"header\"><p style=\"border\:3px; border-style\:solid; border-color\:#FF2121; padding\: 1em;\">Note\: A new GRASS GIS stable version has been released\: <a href=\"https\://grass.osgeo.org/download/\">GRASS GIS 7.8</a>\. Go directly to the new manual page <a href=\"../../../grass78/manuals/libpython/$myfile\">here</a></p>:g" $myfile ; done)


# clean wxGUI sphinx manual etc
(cd $GRASSBUILDDIR/ ; $MYMAKE cleansphinx)

##### generate i18N POT files, needed for https://www.transifex.com/grass-gis/grass7X/
(cd locale ;
$MYMAKE pot
mkdir -p $TARGETDIR/transifex/
cp templates/*.pot $TARGETDIR/transifex/
)

##### generate i18N stats for HTML page path (WebSVN):
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

# package the package
$MYMAKE bindist
if [ $? -ne 0 ] ; then
   halt_on_error "make bindist."
fi

#report system:
echo "System:
$ARCH, compiled with:" > grass-$DOTVERSION\_$ARCH\_bin.txt
## echo "Including precompiled $GDALVERSION library for r.in.gdal" >> grass-$DOTVERSION\_$ARCH\_bin.txt
gcc -v 2>&1 | grep -v Reading >> grass-$DOTVERSION\_$ARCH\_bin.txt

# clean old version off
rm -f $TARGETDIR/grass-$DOTVERSION\_$ARCH\_bin.txt
rm -f $TARGETDIR/grass-$DOTVERSION*.tar.gz
rm -f $TARGETDIR/grass-$DOTVERSION*install.sh

############################################
echo "Copy new binary version into web space:"
cp -p grass-$DOTVERSION\_$ARCH\_bin.txt grass-$DOTVERSION*.tar.gz grass-$DOTVERSION*install.sh $TARGETDIR
rm -f grass-$DOTVERSION\_$ARCH\_bin.txt grass-$DOTVERSION*.tar.gz grass-$DOTVERSION*install.sh

# generate manual ZIP package
(cd $TARGETHTMLDIR/.. ; rm -f $TARGETHTMLDIR/*html_manual.zip ; zip -r /tmp/grass-${DOTVERSION}_html_manual.zip manuals/)
mv /tmp/grass-${DOTVERSION}_html_manual.zip $TARGETHTMLDIR/

# error log etc
cp -f config_$DOTVERSION.git_log.txt $TARGETDIR
cp -f error.log $TARGETDIR
chmod -R a+r,g+w $TARGETDIR     2> /dev/null
chmod -R a+r,g+w $TARGETHTMLDIR 2> /dev/null

echo "Written to: $TARGETDIR"

############################################
# cleanup
cd $GRASSBUILDDIR
$MYMAKE distclean  > /dev/null || (echo "$0: an error occured" ; exit 1)

echo "Finished GRASS $VERSION $ARCH compilation."
echo "Written to: $TARGETDIR"
echo "Copied HTML manual to https://grass.osgeo.org/grass${VERSION}/manuals/"
echo "Copied pygrass progman to https://grass.osgeo.org/grass${VERSION}/manuals/libpython/"
exit 0

