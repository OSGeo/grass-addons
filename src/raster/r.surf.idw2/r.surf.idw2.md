## DESCRIPTION

*r.surf.idw2* fills a raster matrix with interpolated values generated
from a set of irregularly spaced data points using numerical
approximation (weighted averaging) techniques. The interpolated value of
a cell is determined by values of nearby data points and the distance of
the cell from those input points. In comparison with other methods,
numerical approximation allows representation of more complex surfaces
(particularly those with anomalous features), restricts the spatial
influence of any errors, and generates the interpolated surface from the
data points. It is the most appropriate method to apply to most spatial
data. The **npoints** parameter defines the number of points to use for
interpolation. The default is to use the 12 nearest points when
interpolating the value for a particular cell.

## NOTES

The amount of memory used by this program is related to the number of
non-zero data values in the input map layer. If the input raster map
layer is very dense (i.e., contains many non-zero data points), the
program may not be able to get all the memory it needs from the system.
The time required to execute increases with the number of input data
points.

If the user has a mask set, then interpolation is only done for those
cells that fall within the mask. However, all non-zero data points in
the input layer are used even if they fall outside the mask.

This program does not work with latitude/longitude data bases. Another
surface generation program, named
*[r.surf.idw](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw.html)*,
should be used with latitude/longitude data bases.

The user should refer to the manual entries for  
*[r.surf.idw](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw.html)*  
*[r.surf.contour](https://grass.osgeo.org/grass-stable/manuals/r.surf.contour.html)*  
*[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html)*  
to compare this surface generation program with others available in
GRASS.

## KNOWN ISSUES

Module *r.surf.idw* works only for integer (CELL) raster maps.

## SEE ALSO

*[r.surf.contour](https://grass.osgeo.org/grass-stable/manuals/r.surf.contour.html),
[r.surf.idw](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw.html),
[r.surf.gauss](https://grass.osgeo.org/grass-stable/manuals/r.surf.gauss.html),
[r.surf.fractal](https://grass.osgeo.org/grass-stable/manuals/r.surf.fractal.html),
[r.surf.random](https://grass.osgeo.org/grass-stable/manuals/r.surf.random.html),
[r.surf.idw2](https://grass.osgeo.org/grass-stable/manuals/r.surf.idw2.html),
[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html)*

## AUTHOR

Michael Shapiro, U.S.Army Construction Engineering Research Laboratory
