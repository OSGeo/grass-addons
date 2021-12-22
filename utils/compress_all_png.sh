#!/bin/sh
#   compress_all_png.sh
#
#   by Hamish Bowman 14 Apr 2013, Dunedin NZ
#   released to the Public Domain
#
# works its way through the SVN source code tree, finds PNG images, and attempts
# to set the appropriate Subversion props on them & optimize them for size.
# tip: if you have a multi-core machine, why not run on all branches in parallel? :)
#

if [ ! -x "`which optipng`" ] ; then
   echo "This script requires optipng.  Quitting."
   exit 1
fi

if [ ! -x "`which module_svn_propset.sh`" ] ; then
    echo "Could not find module_svn_propset.sh.  Continuing anyway..."
    sleep 3
fi

if [ ! -x "`which svn`" ] ; then
    echo "Could not find Subversion.  Continuing anyway..."
    sleep 3
fi

BUILDDIR="dist.`uname -m`-`uname -p`"

for IMG in `find . | grep -i '\.png$' | grep -v "$BUILDDIR"` ; do
   # avoid running on e.g. d.out.png/ dir and d.out.png script
   if [ -d "$IMG" ] || [ -x "$IMG" ] ; then
     continue
   fi

   module_svn_propset.sh "$IMG"
   optipng -o5 "$IMG" | grep -v '^OptiPNG \|^Copyright '
done


MODIFIED=`svn diff $(find . | grep -i '\.png$' | grep -v "$BUILDDIR") | grep Index | cut -f2- -d' '`
svn diff $MODIFIED

#
## preview & keep an eye out for breakage:
#qiv -f $MODIFIED
#
#svn commit $MODIFIED -m "Run 'optipng -o5' to compress PNG images"
#

