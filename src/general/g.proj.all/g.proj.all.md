## DESCRIPTION

*g.proj.all* reprojects all raster and vector maps from given location
and mapset to the current mapset. If flag `r` is set, current
computational region is used for raster maps reprojection. Otherwise,
each raster map is reprojected to its bounds, ignoring computational
region in the current mapset. Modules
[r.proj](https://grass.osgeo.org/grass-stable/manuals/r.proj.html) and
[v.proj](https://grass.osgeo.org/grass-stable/manuals/v.proj.html) are
used for reprojecting.

## EXAMPLE

This example reprojects raster maps (with resolution 50 map units) and
vector maps from mapset 'landsat' of 'nc\_spm\_08' location to the
current mapset.

```sh
g.proj.all resolution=50 location=nc_spm_08 mapset=landsat
```

## SEE ALSO

*[r.proj](https://grass.osgeo.org/grass-stable/manuals/r.proj.html),
[v.proj](https://grass.osgeo.org/grass-stable/manuals/v.proj.html)*

## AUTHORS

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/),  
Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
