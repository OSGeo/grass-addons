#!/bin/sh
#  Test case for r.surf.volcano: check that resulting raster map
#    is within some arbitrary threshold of matching the map I get.
#    Exits with 0 if everything passed, 1 if something failed.
#  Hamish Bowman Sept. 2024
#
# See gunittest_testing.html's basic example for a pretty relevant
# set of tests. See also r.surf.random's tests for inspiration.

# Tested within the NC sample dataset (nc_spm_08).
g.region n=5120 s=0 w=0 e=5120 res=10

# touches r.mapcalc, g.region, r.info, g.rename, g.remove
r.surf.volcano method=gaussian output="volcano.gauss.$$"

if [ $? -ne 0 ] ; then
   echo "ERROR r.surf.volcano test: did not exit cleanly" 1>&2
   exit 1
fi

eval `r.univar -g "volcano.gauss.$$"`
g.remove -f rast name="volcano.gauss.$$"


# reference values
ref_max=1000
ref_mean=31.3
ref_stddev=121.1

# completely arbitrary cross platform variance threshold
var=5


result=`echo "$max $ref_max $var" | awk \
  'function abs(x){return ((x < 0) ? -x : x)}
   {if( abs($1 - $2) < $3 ) {print "ok"}
   else {print "bad"} }'`

if [ "$result" = "bad" ] ; then
   echo "ERROR r.surf.volcano test: out of bounds raster maximum" 1>&2
   exit 1
fi


result=`echo "$mean $ref_mean $var" | awk \
  'function abs(x){return ((x < 0) ? -x : x)}
   {if( abs($1 - $2) < $3 ) {print "ok"}
   else {print "bad"} }'`

if [ "$result" = "bad" ] ; then
   echo "ERROR r.surf.volcano test: out of bounds raster mean" 1>&2
   exit 1
fi


result=`echo "$stddev $ref_stddev $var" | awk \
  'function abs(x){return ((x < 0) ? -x : x)}
   {if( abs($1 - $2) < $3 ) {print "ok"}
   else {print "bad"} }'`

if [ "$result" = "bad" ] ; then
   echo "ERROR r.surf.volcano test: out of bounds raster std.dev." 1>&2
   exit 1
fi


# all good
exit 0

