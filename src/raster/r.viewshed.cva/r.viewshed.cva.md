## DESCRIPTION

*r.viewshed.cva* is a module that allows for the construction of
"Cumulative Viewshed", or "visualscape" maps from a series of input
points stored in a vector points map. The routine is a python wrapper
script that iterative loops through each input point, calculating a
viewshed map, and then creates an output map that is coded by the number
of input locations that can "see" each cell. *r.viewshed.cva* uses the
GRASS GIS module *r.viewshed* for the viewshed analysis. *r.viewshed* is
very fast, thus allowing for a cumulative viewshed analysis to run in a
reasonable amount of time. The final cumulative viewshed map is computed
using the "count" method of *r.series*, rather than with mapcalc, as it
better handles the null values in the individual constituent viewshed
maps (and allows for interim viewshed maps to be coded in any way).

### Options and flags

*r.viewshed.cva* requires an input elevation map, **input**, and an
input vector points map, **vector**. There is currently only one native
flag for *r.viewshed.cva*, **-k**, which allows you to keep the interim
viewshed maps made for each input point. Optionally, option
**name\_column** can be used with **-k** to specify the suffix of the
kept viewshed maps by a particular column in the input vector points'
database. If no value is specified for **name\_column**, then the cat
value will be used.

All other flags and options are inherited from *r.viewshed* (see the
*[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)*
help page for more information on these).

## NOTES

The input vector points map can be manually digitized (with *v.digit*)
over topographic or cultural features, or can be created as a series of
random points (with *r.random* or *v.random*). Note that using the flag
-k allows you to keep any interim viewshed maps created during the
analysis, and these resultant viewshed maps will be named according to
the cat number of the original input points. This is also useful for
simple creating a large number of individual viewsheds from points in a
vector file.

An automated summit extraction can be done with **r.geomorphon**.

## EXAMPLES

Undertake a cumulative viewshed analysis from a digitized vector points
map of prominent peaks in a region (North Carolina sample dataset):  

```sh
g.region raster=elevation -p
# use v.digit to digitize points or e.g. the r.geomorphon addon for summits
r.viewshed.cva input=elevation output=peaks_CVA_map \
  vector=prominent_peaks_points name_column=cat \
  observer_elevation=1.75 target_elevation=0
```

Undertake a cumulative viewshed analysis from a 10% sample of landscape
locations in a region:  

```sh
g.region raster=elevation -p
r.random input=elevation n=10% vector=rand_points_10p
r.viewshed.cva input=elevation output=peaks_CVA_map \
  vector=rand_points_10p name_column=cat \
  observer_elevation=1.75 target_elevation=0
```

## SEE ALSO

*[r.geomorphon](https://grass.osgeo.org/grass-stable/manuals/r.geomorphon.html),
[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)*

## AUTHOR

Isaac Ullah
