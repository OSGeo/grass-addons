## DESCRIPTION

*i.hyper.export* exports a hyperspectral 3D raster map (`raster_3d`)
from GRASS to an external file. At present, the module supports export
to a **compressed multi-band GeoTIFF** only.

The export process converts the 3D raster map into 2D raster slices
using `r3.to.rast`, creates a temporary imagery group, and writes all
bands into a single multi-band GeoTIFF file with `r.out.gdal`. All
temporary rasters and groups are automatically removed after export.

## FUNCTIONALITY

- Exports the complete hyperspectral 3D raster map as a single
  multi-band GeoTIFF.
- Preserves the spectral band order and spatial alignment of the input
  map.
- Uses **DEFLATE** compression with **PREDICTOR=3** for efficient
  floating-point storage.
- Handles null values as `-9999`.
- Automatically sets the computational region to match the input 3D
  raster map.

## NOTES

- Currently, only multi-band GeoTIFF export is supported.
- All intermediate rasters and imagery groups are temporary and removed
  automatically after export.
- The exported GeoTIFF contains spectral data only; wavelength and other
  metadata remain inside GRASS.
- The output file can be opened in software such as QGIS, ENVI, or
  Python libraries (`rasterio`, `gdal`).

## OPTIONS

- `input` -- Input 3D raster map (required).
- `output` -- Output file name (required). Example:
  `output=prisma_3d.tif`.

## EXAMPLES

::: code

    # Example 1: Export PRISMA 3D raster map to compressed GeoTIFF
    i.hyper.export input=prisma@PERMANENT \
                   output=/data/prisma_3d.tif
:::

## OUTPUT

The output is a **multi-band GeoTIFF** file containing one band per
spectral layer of the 3D raster map. Compression (**DEFLATE** +
**PREDICTOR=3**) ensures compact and precise floating-point storage.
Large files are automatically written as BigTIFF when necessary.

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
