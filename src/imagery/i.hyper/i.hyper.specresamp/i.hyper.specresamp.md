## DESCRIPTION

*i.hyper.specresamp* performs spectral resampling of a hyperspectral 3D
raster map (`raster_3d`). The module takes a hyperspectral cube imported
with [i.hyper.import](i.hyper.import.md) and produces a new 3D raster
whose spectral bands are arranged on a user-defined wavelength grid.

This is useful when harmonizing data from different sensors with
different spectral sampling, or when simulating a multispectral sensor
from hyperspectral data.

## METHODS

Three resampling methods are available:

### Gaussian convolution (default)

Each output band is computed as a weighted average of input bands
based on a Gaussian spectral response function (SRF) centered on the
target wavelength. The width of the Gaussian is controlled by the
FWHM parameter (Schlapfer et al. 1999). This approach is physically
motivated and best suited for sensor simulation or when spectral
response fidelity is important.

### Linear interpolation

A fast method where each output band is linearly interpolated between
the two nearest input bands. This produces a smooth spectral curve and
is appropriate when speed is preferred over exact response function
matching.

### Nearest neighbour

Each output band takes the value of the input band whose center
wavelength is closest to the target. Useful for quick band thinning or
band selection without any spectral mixing.

## NOTES

- **No extrapolation:** Output wavelengths are strictly limited to the
  spectral range of the input raster. Any target wavelength outside
  the input range is silently omitted. To resample to a wider spectral
  range, ensure the input raster covers the desired output range.

  For example, when resampling EnMAP (418.4-2445.3 nm) to PRISMA
  (407.0-2497.1 nm), PRISMA bands below 418.4 nm or above 2445.3 nm
  will be omitted from the output.

- When using the `-v` flag, bands marked as invalid in the input
  metadata (e.g., strong water vapor absorption or sensor artifacts)
  are excluded from the resampling.

- The `-i` flag prints a resampling plan showing input/output band
  counts, spectral ranges, method, and FWHM parameters without
  executing the resampling.

## EXAMPLES

### Resample PRISMA to EnMAP spectral configuration using a reference raster

```bash
i.hyper.specresamp input=prisma@PERMANENT reference=enmap@PERMANENT \
    output=prisma_enmap_gauss method=gaussian -v
```

### Resample using custom uniform wavelength ranges

```bash
i.hyper.specresamp input=prisma output=prisma_resampled \
    wavelengths=400-700,700-2500 fwhm=8.3,11.5 method=gaussian
```

This generates bands on a uniform grid with step = FWHM per range
(e.g., 400-700 nm with 8.3 nm spacing, 700-2500 nm with 11.5 nm
spacing). These FWHM values are typical of the EnMAP sensor
(VNIR ~8.3 nm, SWIR ~11.5 nm).

### Print resampling plan without executing

```bash
i.hyper.specresamp input=prisma reference=enmap -i -v
```

### Example: Linear interpolation

```bash
i.hyper.specresamp input=prisma reference=enmap \
    output=prisma_enmap_linear method=linear
```

### Example: Nearest neighbour

```bash
i.hyper.specresamp input=prisma reference=enmap \
    output=prisma_enmap_near method=nearest
```
