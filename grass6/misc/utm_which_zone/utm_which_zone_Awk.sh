#!/bin/sh

# MN
# calculate UTM zone from LatLong
# DCA
# replace octave with awk. 200511

if [ $# -lt 2 ] || [ -z `which awk` ] ; then
   echo "Requires 'awk' to be installed."
   echo ""
   echo "Usage:  (LONG: x LAT: y)"
   echo "      utm_which_zone.sh LONG LAT"
   exit 1
fi

LONG=$1
LAT=$2

#Original doc from octave version:
# utm_zone.m   Matlab (or gpl'd Octave)
# Calc UTM zone from Lat/Lon position.
#
#  (c) Hamish Bowman, Otago University, New Zealand  (mid 2002 sometime)
#  This program is free software under the GPL (>=v2)
#   for license deails, see  http://www.gnu.org/copyleft/gpl.html
#
# UTM is based on a Transverse Mercator (conformal, cylindrical) projection.
# 60 zones. Width 6deg lon, numbered 1 to 60, starting at 180deg lon (west).
#  8deg lat strips, C to X northwards, omitting I and O, beginning at 80deg
#  south.

awk -v lat=$LAT -v long=$LONG '
BEGIN{
  strips="CDEFGHJKLMNPQRSTUVWX";
  zone = ceil( (long+180)/6.0 );
  strip = substr( strips, ceil((lat+80)/8.0), 1 );
  print "LatLon = " lat " " long;
  print "Zone = " zone;
  print "Strip = " strip;
}
function ceil(x){
  if ( x <= 0 ){
    return int(x);
  }else{
    if ( x == int(x) ){
      return x;
    }else{
      return int(x)+1;
    }
  }
}
'

