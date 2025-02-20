## DESCRIPTION:

The purpose of the *v.rast.bufferstats* module is to provide local
environmental context to a series of input geometries. It computes
statistics from multiple input raster maps within multiple buffers
around selected geometries in the input vector map.

Available statistics are either

1. statistics provided by *r.univar* or
2. if the *t-flag* is checked - area of, number of and/or the most
    frequent (mode) raster categories within the buffers using
    *r.stats*.

If the *output* option is specified, results are written to a text file
or stdout instead of the attribute table of the input map. The output
file is produced with the following column order:  
cat | prefix | buffer| statistic/measure | value  
separated by the user defined separator (default is |).

## NOTE

The module temporarily modifies the computational region. The region is
set to the extent of the respective buffers, while the alignment of the
current region is kept.

## EXAMPLES

```sh
# Preparations
g.region -p raster=elevation,geology_30m
v.clip -r input=bridges output=bridges_wake

# Tabulate area of land cover map
g.region -p raster=elevation,geology_30m align=geology_30m
v.rast.bufferstats -t input=bridges_wake raster=geology_30m buffers=100,250,500 column_prefix=geology

# Compute terrain statistics and update vector attribute table
g.region -p raster=elevation,geology_30m align=elevation
r.slope.aspect elevation=elevation slope=slope aspect=aspect
v.rast.bufferstats input=bridges_wake raster=altitude,slope,aspect buffers=100,250,500 column_prefix=altitude,slope,aspect methods=minimum,maximum,average,stddev percentile=5,95

```

## KNOWN ISSUES

In order to avoid topological issues with overlapping buffers, the
module loops over the input geometries. However, this comes at costs
with regards to performance. For a larger number of geometries in the
vector map, it can be therefore more appropriate to compute neighborhood
statistics with *r.neighbors* and to extract (*v.what.rast*, *r.what*)
or aggregate (*v.rast.stats*) from those maps with neighborhood
statistics.

The module is affected by the following underlying library issue:
Currently, the module uses GRASS native buffering through pygrass which
should be replaced by buffering using GEOS:
https://trac.osgeo.org/grass/ticket/3628

## SEE ALSO

*[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)
[r.stats](https://grass.osgeo.org/grass-stable/manuals/r.stats.html)
[v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html)*

## AUTHOR

Stefan Blumentrath, Norwegian Institute for Nature Research, Oslo,
Norway
