## DESCRIPTION

Note: this module is superseded by
[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html).

*r.out.tiff* converts a GRASS raster map to a TIFF raster map. Output
may be 8 or 24 bit (TrueColor). Optionally, a TIFF World file compatible
with ESRI's and other's products may be output.

The program prompts the user for the name of a GRASS raster map, an
output TIFF file, whether an 8 or 24 bit format is desired, and whether
or not to create a TIFF world file. Currently only uncompressed,
packpit, or deflate TIFF files are written. These output formats are
known to be compatible with r.in.tiff.

The output filename will always have the suffix `.tif`, and the Tiff
World file (if requested) `.tfw`. Any `.tif` or `.tiff` suffix (case
insensitive) specified in the output filename will be discarded.

When writing with "-l" option, tiles are written at 128x128 pixels. For
programs that can utilize tiles, it can help speed up some drawing
operations.

The user may adjust region and resolution before export using
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html).

A better choice to export GRASS raster data might be
[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html).

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.in.gdal](https://grass.osgeo.org/grass-stable/manuals/r.in.gdal.html),
[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html)*

## AUTHOR

Michael Shapiro, U.S. Army Construction Engineering Research Laboratory

GRASS 5.0 team
