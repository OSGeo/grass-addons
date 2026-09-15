## DESCRIPTION

*r.out.ntv2* converts a pair of GRASS raster maps containing longitude
and lattitude coordinate offsets into an [NTv2 grid datum
shift](https://proj.org/usage/transformation.html?highlight=nadgrids#grid-based-datum-adjustments)
file.

## NOTES

NTv2 format supports only single-precission floating point data. GRASS
GIS double-precision DCELL data need to be reduced to FCELL before
export, eg. using
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)
`float()` function.

The user should adjust the region and resolution to match the input
raster maps before export, using
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html).

PROJ.4 and the software that depend on it, including GDAL, GRASS, QGIS,
assume the NTv2 grid's destination coordinate system to be WGS84. The
metadata values in the grid's header set with `majort`, `minort`,
`systemt` parameters are ignored, same as the input coordinate system
parameters (`majorf`, `minorf`, `systemf`). They are for documentation
purposes only.

The `CREATED` and `UPDATED` output grid's metadata fields are set to,
respectively, current date and time, in YYYYMMDD and HHMMSS format.

## SEE ALSO

[NTv2 format description by
ESRI](https://github.com/Esri/ntv2-file-routines)

## AUTHOR

Maciej Sieczka
