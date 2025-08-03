## DESCRIPTION

*i.segment.stats* calculates statistics for areas in a raster map. Areas
are defined by adjacent pixels with the same value. Such areas can be
the output of
*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)*
or
*[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html)*.

Available statistics are those related to the shape, size and position
of the areas (see the
*[r.object.geometry](https://grass.osgeo.org/grass-stable/manuals/r.object.geometry.html)*
man page for more information on the statistics) and aggregated
statistics of pixel values of other raster maps (see
*[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)*
for details).

In addition, for each of the above statistics, the **-n** flag allows
the user to request the output of the mean and the standard deviation of
the values of the neighboring objects (all direct neighbors, diagonal
neighbors included), which allows gathering some context information for
each object. For this feature, the
*[r.neighborhoodmatrix](r.neighborhoodmatrix.md)* addon has to be
installed. Currently, the module calculates these context statistics for
all available shape and spectral statistics.

The user can chose between output in the form of a vector map of the
areas with the statistics in the attribute table (**vectormap**) and/or
in the form of a CSV text file (**csvfile**).

Because of the way
*[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)*
functions, it is difficult to handle cases where in some raster maps
values are all null in some of the areas. Because of this,
*i.segment.stats* checks the raster maps for existing null values and
excludes them if it find any, emitting a warning to inform the user. The
user can decide to ignore this check using the **c** flag, for example
when there are only a few null cells and no complete areas with only
null cells (i.e. the module can calculate statistics for areas with some
null cells in them).

## NOTES

The module respects the current region settings. The **-r** flag allows
to force the module to adjust the region to the input raster map before
calculating the statistics.

This module is a simple front-end to
*[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)*
and
*[r.object.geometry](https://grass.osgeo.org/grass-stable/manuals/r.object.geometry.html)*.
If other statistics are desired, these should probably be implemented in
those (or other) modules which can then be called from this module.

Problems can arise in the calculation of some form statistics for
certain segment forms. If errors arise, the user might want to try to
run
*[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html)*
on the input raster file before running *i.segment.stats*.

When treating files with a large number objects, creating the vector map
can be very time-consuming. In that case, it might be easier to only
work with the **csvfile** output.

The processing of several raster input files for which to calculate
per-segment statistics can be parallelized by setting the **processes**
parameter to the number of desired parallel processes, with at most one
process per raster to be treated.

## EXAMPLE

```sh
i.group group=landsat_pan input=lsat7_2002_80
g.region rast=lsat7_2002_80 -p
i.segment group=landsat_pan output=ls_pan_seg01 threshold=0.1 memory=4000 minsize=50
i.segment.stats map=ls_pan_seg01 csvfile=segstats.csv vectormap=ls_pan_seg01 \
  rasters=lsat7_2002_10,lsat7_2002_20,lsat7_2002_30,lsat7_2002_40,lsat7_2002_50,lsat7_2002_70 \
  processes=4
```

## SEE ALSO

*[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html),
[r.univar](https://grass.osgeo.org/grass-stable/manuals/r.univar.html),
[v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html),
[r.object.geometry](https://grass.osgeo.org/grass-stable/manuals/r.object.geometry.html)*

*[v.class.mlR (Addon)](v.class.mlR.md)*

## AUTHOR

Moritz Lennert
