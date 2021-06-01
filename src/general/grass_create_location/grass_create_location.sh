#!/bin/sh

############################################################################
#
# MODULE:       grass_create_location.sh
# AUTHOR(S):    Markus Neteler
# PURPOSE:      Create new GRASS location from outside GRASS session
# COPYRIGHT:    (C) 2009, 2011 by the GRASS Development Team, Markus Neteler
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
#############################################################################

# find GRASS installation
if [ ! -x "`which grass64`" ] ; then
   if [ ! -x "`which grass65`" ] ; then
      echo "GRASS GIS installation is required, please install it first"
      exit 1
   else
      GRASSSTART=`which grass65`
   fi
else
   GRASSSTART=`which grass64`
fi
GRASSBINS=`grep "^GISBASE=" ${GRASSSTART} | cut -d'=' -f2 | sed 's+"++g'`
echo "Using GRASS installation in <$GRASSBINS>"

if test "$GISBASE" != ""; then
    echo "You must run this script outside of a GRASS GIS session." >&2
    exit 1
fi

if [ $# -ne 3 ] ; then
   echo "Usage: $0 <type> <filename>|<epsgcode> <location>"
   echo ""
   echo "type: gisfile,wktfile,epsgcode"
   echo ""
   echo "Examples:"
   echo "  $0 province.shp latlong"
   echo "  $0 myfile.wkt latlong"
   echo "  $0 4326 latlong"
   exit 1
fi

TYPE=$1
INPUT=$2
LOCATION=$3

# SET ONCE ONLY: path to GRASS binaries and libraries:
export GISBASE=$GRASSBINS
export PATH=$PATH:$GISBASE/bin:$GISBASE/scripts
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:$GISBASE/lib
# ACTUAL SESSION: use process ID (PID) as lock file number:
export GIS_LOCK=$$
# path to GRASS settings file
export GISRC=$HOME/.grassrc6

# check if raster or vector
if [ "$TYPE" = "gisfile" ] ; then
   gdalinfo ${INPUT} 2>/dev/null
   if [ $? -ne 0 ] ; then
      ogrinfo ${INPUT} 2>/dev/null
      if [ $? -ne 0 ] ; then
         echo "ERROR: Cannot open data source (not GDAL/OGR supported file)"
         exit 1
      fi
   fi
else
  echo ""
fi

# the real job
if [ "$TYPE" = "gisfile" ] ; then
   g.proj -c georef=$INPUT location=$LOCATION
   if [ $? -ne 0 ] ; then
      echo "ERROR: could not create GRASS location"
   fi
else
   if [ "$TYPE" = "wktfile" ] ; then
      g.proj -c wkt=$INPUT location=$LOCATION
   else
      if [ "$TYPE" = "epsgcode" ] ; then
         g.proj -c epsg=$INPUT location=$LOCATION
      else
         echo "ERROR: No idea what you specified as 'type'"
         exit 1
      fi
   fi
fi

exit 0
