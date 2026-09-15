## DESCRIPTION

Module *r.divergence* computes the divergence of a vector field given by
**magnitude** and **direction** raster maps. Direction is in degrees
counterclockwise from the east and can be computed using
*[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html)*.
This module can be used for estimating erosion and deposition rates for
a steady state overland flow using USPED (Unit Stream Power based
Erosion Deposition) model. Net erosion/deposition is estimated as a
change in sediment flow rate expressed by a divergence in sediment flow.

## EXAMPLES

In North Carolina sample dataset, we compute net erosion/deposition.

```sh
g.region raster=elev_lid792_1m -p
r.slope.aspect elevation=elev_lid792_1m slope=slope aspect=aspect
r.flow elevation=elev_lid792_1m flowaccumulation=flowacc

# exponents m=1.3 and n=1.2
# multiply flowaccumulation by cell area/resolution to get contributing area per unit width
r.mapcalc "sflowtopo = pow(flowacc * 1.,1.3) * pow(sin(slope),1.2)"

# Compute sediment flow by combining the rainfall, soil and land cover factors
# with the topographic sediment transport factor.
# We use a constant value of 270. for rainfall intensity factor.
r.mapcalc "sedflow = 270. * soils_Kfactor * cfactorbare_1m * sflowtopo"
r.divergence magnitude=sedflow direction=aspect output=erosion_deposition

# set suitable color table
r.colors map=erosion_deposition rules=- << EOF
0% 100 0 100   #dark magenta
-100 magenta
-10 red
-1 orange
-0.1 yellow
0 200 255 200     #light green
0.1 cyan
1 aqua
10 blue
100 0 0 100       #dark blue
100% black
EOF
```

## SEE ALSO

*[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html)*

## AUTHORS

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)  
Helena Mitasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
