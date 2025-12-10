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

## POSSIBLE ROAD MAP

- Importers for additional data (OCI, HySIS, EMIT, DESIS, Hyperion)
- Additional preprocessing modules (e.g., wavelet transform)
- Smarter metadata handling
- Standardized export formats (Zarr, HDF5) (metadata in headers or separate files)
- Aerial imagery module with multi-sensor harmonization
- Atmospheric correction from radiance to reflectance
- Integration of field spectrometry data
- Support for regression and classification tasks
- Improved read and write performance (including faster 3D garray access)
- Refactoring Python components to native GRASS where possible
- 3D hyperspectral cube visualization

## DEPENDENCIES

*i.hyper.\** modules require the following Python libraries for full
functionality:

- NumPy
- SciPy
- scikit-learn
- Matplotlib
- h5py
- rasterio
- pyproj

The *i.hyper.explore* module requires the GRASS addon *r3.what\**

After dependencies are installed, the toolset can be added to GRASS
using:

::: code

    g.extension extension=i.hyper
:::

## SEE ALSO

*[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html),
[i.hyper.composite](i.hyper.composite.html),
[i.hyper.export](i.hyper.export.html)
[r3.what](https://grass.osgeo.org/grass-stable/manuals/addons/r3.what.html)*

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
