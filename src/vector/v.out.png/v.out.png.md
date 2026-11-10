## DESCRIPTION

*v.out.png* exports a GRASS vector map in non-georeferenced Portable
Network Graphics (PNG) image format, respecting the current region
resolution and bounds. By default it look for a color table, set using
[v.colors](https://grass.osgeo.org/grass-stable/manuals/v.colors.html)
you can also set the attribute table where read the feature color.

Optionally the user can choose to export a World File (.wld) to provide
basic georeferencing support using the **-w** flag.

## SEE ALSO

*[r.out.png](https://grass.osgeo.org/grass-stable/manuals/r.out.png.html),
[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html),
[r.in.png](https://grass.osgeo.org/grass-stable/manuals/r.in.png.html),
[v.colors.png](https://grass.osgeo.org/grass-stable/manuals/v.colors.html)*

## AUTHORS

Luca Delucchi  
World file support by Anika Bettge and Markus Neteler
