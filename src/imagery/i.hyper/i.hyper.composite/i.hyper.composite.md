## DESCRIPTION

*i.hyper.composite* creates RGB, CIR, SWIR and custom false-color
composites from a hyperspectral 3D raster map (`raster_3d`). The module
reads per-band wavelength metadata from the 3D raster (as written by
[i.hyper.import](i.hyper.import.html) /
[i.hyper.preproc](i.hyper.preproc.html)), selects the nearest available
bands to requested wavelengths, enhances contrast, and composes a 2D
color raster.

Internally, the cube is temporarily exploded into 2D rasters (one per
band) using `r3.to.rast`. For each composite, the nearest bands to
target wavelengths are chosen, optional color enhancement is applied
with `i.colors.enhance`, and the final composite is produced with
`r.composite`. Temporary rasters and the temporary region are
automatically cleaned up.

Predefined composites are provided for common use-cases; custom triplets
(R,G,B in nm) are supported for sensor-agnostic workflows.

## FUNCTIONALITY

Built-in composites (target wavelengths in nm):

- **rgb** --- \[660, 572, 478\] (true color)
- **cir** --- \[848, 660, 572\] (color-infrared)
- **swir_agriculture** --- \[848, 1653, 660\] (vegetation/wetness
  contrast)
- **swir_geology** --- \[2200, 848, 572\] (mineral/rock contrast)

**Custom composite:** specify `composites_custom=R,G,B` (wavelengths in
nm), e.g. `2200,848,572` or `560,860,1640`. The module selects the
nearest available band to each requested wavelength; it does not
resample spectrally.

## NOTES

- The input 3D raster must contain per-band wavelength comments in
  `r3.info` (e.g., lines like `Band 17: 848 nm`); otherwise the module
  aborts with a clear error.
- Nearest-band selection is used (no spectral resampling). If your
  cube's wavelengths differ from the requested targets, the closest
  bands are chosen.
- `i.colors.enhance` is run with the provided `strength` (0--100). For
  the **rgb** composite, the `-p` flag is used to preserve natural RGB
  balance; other composites run without `-p`.
- A temporary 3D region is set to the cube; the original region is
  restored. Temporary 2D rasters are removed on exit.
- Requires at least 3 bands in the input cube.

## OPTIONS

- `map` --- input hyperspectral 3D raster map (required).
- `output` --- output name prefix for generated composites (required).
- `composites=rgb,cir,swir_agriculture,swir_geology` --- list of presets
  to create (optional, multiple allowed).
- `composites_custom=R,G,B` --- custom wavelengths in nm, e.g.
  `2200,848,572` (optional).
- `strength` --- enhancement strength for `i.colors.enhance` (0--100,
  default: 96).

## EXAMPLES

::: code

    # Set the region
    g.region raster_3d=prisma

    # Example 1: True color (RGB) and CIR from PRISMA
    i.hyper.composite map=prisma output=prisma \
                      composites=rgb,cir

    # Console output:
    Generated composite raster: prisma_rgb
    Generated composite raster: prisma_cir
:::

::: code

    # Example 2: SWIR geology composite from EnMAP

    # Set the region
    g.region raster_3d=enmap

    i.hyper.composite map=enmap output=enmap \
                      composites=swir_geology strength=90

    # Console output:
    Generated composite raster: enmap_swir_geology
:::

::: code

    # Example 3: Custom Snow/Ice composite (Green–NIR–SWIR)

    # Set the region
    g.region raster_3d=tanager

    # Uses nearest bands to 560, 860, and 1640 nm
    i.hyper.composite map=tanager output=snowice \
                      composites_custom=560,860,1640 strength=92

    # Console output:
    Generated composite raster: snowice_custom
:::

## SEE ALSO

[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html),
[i.hyper.export](i.hyper.export.html),
[r3.to.rast](https://grass.osgeo.org/grass-stable/manuals/r3.to.rast.html),
[r.composite](https://grass.osgeo.org/grass-stable/manuals/r.composite.html),
[i.colors.enhance](https://grass.osgeo.org/grass-stable/manuals/i.colors.enhance.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r3.info](https://grass.osgeo.org/grass-stable/manuals/r3.info.html)

## AUTHORS

Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
