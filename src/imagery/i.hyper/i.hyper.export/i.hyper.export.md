## DESCRIPTION

*i.hyper.export* exports a hyperspectral 3D raster map (`raster_3d`)
from GRASS to an external file. The module supports export to a
**compressed multi-band GeoTIFF** or a native `.ihyper` gzip archive.

The export process converts the 3D raster map into 2D raster slices
using `r3.to.rast`, creates a temporary imagery group, and writes all
bands into a single multi-band GeoTIFF file with `r.out.gdal`. All
temporary rasters and groups are automatically removed after export.

*i.hyper.export* can also write a native `.ihyper` gzip archive for
exact transfer of a hyperspectral `raster_3d` (inspired by `r.pack`).
This stores the full map in native GRASS form together with
`hyper.json`; related composites can be included optionally, but are not
exported by default.

## FUNCTIONALITY

- Exports the complete hyperspectral 3D raster map as a single
  multi-band GeoTIFF or native `.ihyper` archive.
- Preserves the spectral band order and spatial alignment of the input
  map.
- Uses **DEFLATE** compression with **PREDICTOR=3** for efficient
  floating-point storage.
- Handles null values as `-9999`.
- Automatically sets the computational region to match the input 3D
  raster map.

## NOTES

- Native `.ihyper` export stores the complete `grid3` map directory
  together with `hyper.json`.
- All intermediate rasters and imagery groups are temporary and removed
  automatically after export.
- The exported GeoTIFF contains spectral data only; wavelength and other
  metadata remain inside GRASS.
- The output file can be opened in software such as QGIS, ENVI, or
  Python libraries (`rasterio`, `gdal`).
- Existing related composites can be included in `.ihyper` export
  optionally with the `-c` flag.

## OPTIONS

- `input` -- Input 3D raster map (required).
- `output` -- Output file name (required). Example:
  `output=prisma_3d.tif`.
- `format` -- Export format: `gtiff` or `ihyper`.

## EXAMPLES

::: code

    # Example 1: Export PRISMA 3D raster map to compressed GeoTIFF
    i.hyper.export input=prisma@PERMANENT \
                   output=/data/prisma_3d.tif
:::

::: code

    # Export native hyperspectral archive
    i.hyper.export input=p2ld \
                   output=/data/hyperspectral_data.ihyper \
                   format=ihyper

    # Export native hyperspectral archive and include existing composites
    i.hyper.export input=p2ld \
                   output=/data/hyperspectral_data.ihyper \
                   format=ihyper -c
:::

## OUTPUT

The output is a **multi-band GeoTIFF** file containing one band per
spectral layer of the 3D raster map. Compression (**DEFLATE** +
**PREDICTOR=3**) ensures compact and precise floating-point storage.
Large files are automatically written as BigTIFF when necessary.

## SEE ALSO

[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.metadata](i.hyper.metadata.html),
[i.hyper.explore](i.hyper.explore.html),
[r.pack](https://grass.osgeo.org/grass-stable/manuals/r.pack.html)

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
