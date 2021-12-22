#!/bin/sh

# helper script to calculate pre-release event dates according to
# https://trac.osgeo.org/grass/wiki/RFC/4_ReleaseProcedure
# 
# Markus Neteler, 2017


for d in 0 30 40 55 ; do
  delay=7 # between this first announcement and day X
  d=`expr $d + $delay`
  date -d "now +$d days" +"%Y-%m-%d"
done
