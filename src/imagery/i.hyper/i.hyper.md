---
name: i.hyper
description: i.hyper family modules
---

## DESCRIPTION

The purpose of *i.hyper* is to provide a complete toolset for
hyperspectral data processing in GRASS. It enables importing,
preprocessing, visualization and exporting of hyperspectral datasets
(`raster_3d`).

## NOTES

Modules in the *i.hyper* suite operate together to handle hyperspectral
workflows. They include tools for data import, spectral preprocessing,
visualization, and export, fully integrated with the GRASS 3D raster
environment.

The *i.hyper* toolset requires GRASS 8.5 or newer.

## POSSIBLE ROAD MAP

- Integration of wavelength units into default 3D raster metadata
- Atmospheric correction from radiance to reflectance
- Integration of field spectrometry data
- Support for regression and classification tasks
- Improved read and write performance, including faster 3D `garray` access
- 3D hyperspectral cube visualization
- Importers for additional data (OCI, HySIS, EMIT, DESIS, Hyperion)
- Additional preprocessing modules (for example wavelet transform)
- Aerial imagery modules with multi-sensor harmonization
- Refactoring Python components to native GRASS where possible
- Tutorial and example workflows

## DEPENDENCIES

Core Python dependency:

- NumPy

Optional dependencies by module or format:

- SciPy: preprocessing utilities
- scikit-learn: dimensionality reduction in `i.hyper.preproc`
- Matplotlib: plotting in `i.hyper.explore`
- rasterio: EnMAP import
- pyproj: PRISMA and Tanager georeferencing helpers
- h5py: PRISMA and Tanager import, and HDF5 export
- zarr: Zarr export
- GDAL Python bindings (`osgeo.gdal`): GeoTIFF metadata writing in `i.hyper.export`
- GDAL command line tools (`gdalwarp`): EnMAP L1B import

Additional GRASS addon:

- `r3.what`: required by `i.hyper.explore`

After dependencies are installed, the toolset can be added to GRASS
using:

::: code

    g.extension extension=i.hyper
:::

## SEE ALSO

*[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.metadata](i.hyper.metadata.html),
[i.hyper.explore](i.hyper.explore.html),
[i.hyper.composite](i.hyper.composite.html),
[i.hyper.export](i.hyper.export.html)
[r3.what](https://grass.osgeo.org/grass-stable/manuals/addons/r3.what.html)*

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
