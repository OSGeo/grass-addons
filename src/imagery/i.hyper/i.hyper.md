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
