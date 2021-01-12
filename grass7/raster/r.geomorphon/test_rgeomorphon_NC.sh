#!/bin/sh

# 2017, Markus Neteler
# synthetic test case for r.geomorphon 

GRASSDATA=$HOME/grassdata

grass72 $GRASSDATA/nc_spm_08_grass7/user1/

# computational region of NC
g.region raster=elevation -p

# generate a synthetic, non-symmetric DEM
r.mapcalc "synthetic_dem = sin(x() / 5.0) + (sin(x() / 5.0) * 100.0 + 200)"

# d.mon wx0
# d.rast synthetic_dem

# calculate geomorphon forms
r.geomorphon elevation=synthetic_dem forms=synthetic_dem_geomorph search=10

# expected result:
r.category synthetic_dem_geomorph
#1	flat
#3	ridge
#4	shoulder
#6	slope
#8	footslope
#9	valley


# further visual inspection
# d.rast synthetic_dem_geomorph
# r.relief synthetic_dem out=synthetic_dem_shaded
# d.shade shade=synthetic_dem_shaded color=synthetic_dem_geomorph

