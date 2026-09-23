## DESCRIPTION

*v.area.weigh* rasterizes vector areas using known cell weights. In the
output raster, the sum off all cells falling into a given area is
identical to the area attribute value used to rasterize the area.

*v.area.weigh* can add spatial detail to larger areas, if more detailed
information is available from other sources. For example, population
counts are typically available for administrative areas such as
provinces, counties or countries. At the same time, the location of
urban areas might be known and can be used to refine spatial detail
using *v.area.weigh*.

## SEE ALSO

*[v.surf.mass](v.surf.mass.md) addon,
[r.area.createweight](r.area.createweight.md) addon,
[v.to.rast](https://grass.osgeo.org/grass-stable/manuals/v.to.rast.html),
[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html)*

## AUTHOR

Markus Metz
