## DESCRIPTION

*r.stream.slope* calculates local downstream elevation change and local
downstream minimum and maximum curvature.

## OPTIONS

  - *direction*  
    Flow direction: name of input direction map produced by
    *r.watershed* or *r.stream.extract*. If r.stream.extract output map
    is used, it only has non-NULL values in places where streams occur.
    NULL (nodata) cells are ignored, zero and negative values are valid
    direction data if they vary from -8 to 8 (CCW from East in steps of
    45 degrees). Direction map shall be of type CELL values. Region
    resolution and map resolution must be the same.
  - *elevation*  
    Elevation: name of input elevation map or any other map we want to
    calculate. Map can be of type CELL, FCELL or DCELL. It is not
    restricted to resolution of region settings like *direction*.
  - *difference*  
    Output downstream elevation difference: difference between elevation
    of current cell and downstream cell. Shall always be positive.
    Negative values show, that current cell is pit or depression cell.
    Module is prepared to be used with elevation but can be also used to
    calculate local difference of any feature along watercourses in
    slope subsystem. In that way elevation map must be replaced by map
    we want to calculate. If we use different map than elevation, rest
    of parameters have no sense to calculate
  - *gradient*  
    Output downstream gradient: Downstream elevation difference divided
    by distance.
  - *maxcurv*  
    Output maximum linear curvature along watercourse. Calculated along
    watercourse between highest upstream cell, current cell and
    downstream cell (there can be only one or no downstream cell but
    more than on upstream)
  - *mincurv*  
    Output minimum linear curvature along watercourse. Calculated along
    watercourse between lowest upstream cell, current cell and
    downstream cell (there can be only one or no downstream cell but
    more than on upstream)

## EXAMPLE

```sh
g.region -p -a raster=elevation
r.watershed elevation=elevation threshold=10000 drainage=dirs stream=streams
r.stream.slope dir=dirs elevation=elevation difference=downstream_elev_difference \
  gradient=downstream_gradient maxcurv=downstream_maxcurv mincurv=downstream_mincurv
```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.stream.channel](r.stream.channel.md),
[r.stream.distance](r.stream.distance.md),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.order](r.stream.order.md),
[r.stream.segment](r.stream.segment.md),
[r.stream.snap](r.stream.snap.md), [r.stream.stats](r.stream.stats.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

See also [r.streams.\*
modules](https://grasswiki.osgeo.org/wiki/R.stream.*_modules) wiki page.

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
