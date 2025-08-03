## DESCRIPTION

*r.cell.area* uses the current computational region to compute the area
of each raster cell. It can do so on a projected coordinate system or on
a geographic coordinate system; the latter is accomplished via the
latitude of the cell's midpoint. This approximation can generate \~1%
error with coarse lat/lon cells near the poles.

## NOTES

Output units can be either square meters or square kilometers. This
module is useful for determining the flow accumulation area to weight
flow accumulation algorithms by rainfall and/or on lat/lon grids.

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## AUTHOR

Andrew D. Wickert
