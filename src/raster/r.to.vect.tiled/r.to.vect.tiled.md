## DESCRIPTION

*r.to.vect.tiled* vectorizes the **input** raster map and produces
several tiled vector maps covering the current region.

Vectorizing a large raster map with *r.to.vect* can require a lot of
memory. In these cases, *r.to.vect.tiled* can reduce memory usage by
vectorizing each tile separately.

The tiles are optionally patched together with the *-p* flag.

## SEE ALSO

*[r.to.vect](https://grass.osgeo.org/grass-stable/manuals/r.to.vect.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[v.patch](https://grass.osgeo.org/grass-stable/manuals/v.patch.html),
[r.thin](https://grass.osgeo.org/grass-stable/manuals/r.thin.html),
[v.clean](https://grass.osgeo.org/grass-stable/manuals/v.clean.html)*

## AUTHOR

Markus Metz
