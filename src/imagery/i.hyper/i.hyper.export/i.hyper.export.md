## DESCRIPTION

*i.hyper.export* exports a hyperspectral 3D raster map (`raster_3d`)
from GRASS to an external file. By default, the module writes a native
`.ihyper` gzip archive. It also supports export to **compressed
multi-band GeoTIFF**, **HDF5**, or **Zarr**.

The export process converts the 3D raster map into 2D raster slices
using `r3.to.rast`, creates a temporary imagery group, and writes all
bands into a single multi-band GeoTIFF file with `r.out.gdal`. All
temporary rasters and groups are automatically removed after export.

*i.hyper.export* can also write a native `.ihyper` gzip archive for
exact transfer of a hyperspectral `raster_3d` (inspired by `r.pack`).
This stores the full map in native GRASS form together with
`hyper.json`; related composites can be included optionally, but are not
exported by default. HDF5 and Zarr exports write the cube in
`(band,row,col)` order, where the first axis is the spectral axis.

## FUNCTIONALITY

- Exports the complete hyperspectral 3D raster map as a single
  multi-band GeoTIFF, HDF5 cube, Zarr cube, or native `.ihyper`
  archive.
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
- The exported GeoTIFF keeps spatial georeferencing and embeds
  hyperspectral dataset metadata together with per-band wavelength,
  FWHM, and validity metadata from `hyper.json`.
- HDF5 and Zarr exports store the full hyperspectral cube in
  `(band,row,col)` order and include both the full `hyper.json`
  metadata payload and spatial metadata needed to interpret the cube.
- The output file can be opened in software such as QGIS, ENVI, or
  Python libraries (`rasterio`, `gdal`, `h5py`, `zarr`).
- Existing related composites can be included in `.ihyper` export
  optionally with the `-c` flag.

## OPTIONS

- `input` -- Input 3D raster map (required).
- `output` -- Output file name (required). Example:
  `output=prisma_3d.ihyper`.
- `format` -- Export format: `ihyper` (default), `gtiff`, `h5`, or `zarr`.
- `chunks` -- Chunk sizes in `band,row,col` order. The first value is
  the spectral axis. This option is shown for all formats but used only
  for `h5` and `zarr`. Use `0,0,0` for automatic chunk sizes.

## EXAMPLES

::: code

    # Example 1: Export PRISMA 3D raster map to native .ihyper archive (default)
    i.hyper.export input=prisma@PERMANENT \
                   output=/data/prisma_3d.ihyper
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

    # Export as HDF5 cube with explicit chunk sizes in band,row,col order
    i.hyper.export input=p2ld \
                   output=/data/hyperspectral_data.h5 \
                   format=h5 \
                   chunks=8,256,256

    # Export as Zarr cube with automatic chunk sizes
    i.hyper.export input=p2ld \
                   output=/data/hyperspectral_data.zarr \
                   format=zarr \
                   chunks=0,0,0
:::

## OUTPUT

The output is a native `.ihyper` archive by default, or a **multi-band
GeoTIFF**, **HDF5**, or **Zarr** dataset when `format=` is set
explicitly. GeoTIFF uses compression (**DEFLATE** + **PREDICTOR=3**) and
stores per-band hyperspectral metadata. HDF5 and Zarr store the full
cube in `(band,row,col)` order together with embedded metadata.

## SEE ALSO

[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.metadata](i.hyper.metadata.html),
[i.hyper.explore](i.hyper.explore.html),
[r.pack](https://grass.osgeo.org/grass-stable/manuals/r.pack.html)

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
