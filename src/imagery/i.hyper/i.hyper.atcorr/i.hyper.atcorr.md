## DESCRIPTION

*i.hyper.atcorr* performs atmospheric correction of a hyperspectral 3D
raster map. The input is calibrated top of atmosphere radiance. Radiance per
nanometre or per micrometre is converted internally to W m-2 sr-1 um-1. The
output is unitless bottom of atmosphere surface reflectance.

The module uses the 6SV2.1 radiative transfer model to compute a lookup
table for aerosol optical depth (AOD) at 550 nm, column water vapour, and
wavelength. Radiance values are converted to top of atmosphere reflectance
using the acquisition day, solar zenith angle, and the solar irradiance
spectrum. Surface reflectance is then obtained by interpolation in the
lookup table.

The lookup table can be written to a file with *lut*. If *input* and
*output* are given, the table is also applied to the input 3D raster map.
At least one of *lut* or *output* must be specified.

Atmospheric conditions can be supplied as scene values with *aod_val* and
*h2o_val*, or as raster maps with *aod_map* and *h2o_map*. Raster map values
take precedence over scene values where they are not null. The atmospheric
maps can be smoothed before correction.

The module can estimate selected atmospheric quantities from bands in the
input map. It can also apply adjacency, terrain illumination, and surface
anisotropy corrections. Optional outputs include reflectance uncertainty,
a quality mask, and the directional area scattering factor (DASF).

## OPTIONS

The module has two operating forms. With *lut* only, it computes and writes
the lookup table. With *input* and *output*, it computes surface reflectance.
Both forms can be used in one invocation.

The *aod* and *h2o* options define the lookup table axes. The wavelength axis
is defined by *wl_min*, *wl_max*, and *wl_step*. These options use
nanometres. The axes should cover the atmospheric values and wavelengths in
the input map.

The atmosphere can be represented by one of the standard profiles selected
with *atmosphere*. The aerosol model is selected with *aerosol*. When
*aerosol=custom* is used, *mie_r*, *mie_sigma*, *mie_mr*, and *mie_mi*
define the particle size distribution and refractive index.

Flags *-a*, *-w*, and *-z* estimate AOD, water vapour, and ozone from the
input map. Flag *-p* estimates surface pressure from the oxygen A band.
Flag *-e* performs a joint AOD and water vapour retrieval. These operations
require wavelength metadata for the input bands. The *dem* option instead
uses mean terrain elevation to set surface pressure for lookup table
computation.

The *slope* and *aspect* raster maps enable terrain illumination correction.
They must be supplied together. The *sun_azimuth* option or corresponding
scene metadata supplies the solar azimuth. Per pixel view geometry can be
given with *view_zenith* for terrain path-length correction and with
*view_zenith* and *view_azimuth* for BRDF normalization.

The *brdf_fiso*, *brdf_fvol*, and *brdf_fgeo* raster maps enable nadir BRDF
adjusted reflectance normalization. All three maps are required. The
*mcd43_fiso*, *mcd43_fvol*, and *mcd43_fgeo* options provide spectral MCD43
kernel weights. These three options must also be supplied together.

Flag *-u* computes reflectance uncertainty. The result is written when
*uncertainty* is specified. Flag *-m* computes the quality mask written with
*quality*. Flag *-D* computes DASF and writes it with *dasf*. Flag *-r*
applies surface prior regularisation and requires the complete reflectance
cube to be held in memory.

## NOTES

The input must contain calibrated spectral radiance. Per-nanometre and
per-micrometre radiance units in the hyperspectral metadata are supported.
Reflectance input is not supported. Output reflectance is limited
to the interval from -0.01 to 1.5. If radiometric units are absent, the module
warns and assumes radiance per micrometre.

Band centre wavelengths are read from hyperspectral metadata managed by
*[i.hyper.metadata](i.hyper.metadata.md)*. The module can also read band
entries in 3D raster history in the form `Band N: WL nm`. Band width metadata
is used by operations which account for the spectral response. Metadata
wavelengths may use nm, um, or cm-1 and are converted internally to
micrometres. Image based retrievals require suitable bands within the spectral
range of the input.

Scene geometry and atmospheric values are resolved in the following order:
command line option, input map metadata, and module default. Solar zenith is
required when it is not present in the metadata. Command line values override
metadata values.

The day of year must be between 1 and 365. It is used for the Earth to Sun
distance correction. The solar and view angles must describe the acquisition
geometry of the input map.

The lookup table axes should include the expected AOD and water vapour
values. Values outside an axis are limited to the nearest table boundary.
A finer table increases computation and memory use.

The 2D ancillary raster maps are read in the current computational region.
Set the region to the horizontal extent and resolution of the input 3D raster
map before running the module. Null radiance cells remain null in the output.
Non-positive radiance cells and bands with round-trip transmittance below 0.10
are also written as null.

The *lut* file records the table computed by the current invocation. It is an
output file and is not read by this module. Information about the file format,
the radiative transfer implementation, and library interfaces is available
from the reference implementation listed below.

Surface prior regularisation, uncertainty calculation, DASF retrieval, and
some image based retrievals need additional arrays for the complete scene.
Memory use therefore increases with the number of cells and bands.

## EXAMPLES

The following command computes a lookup table without correcting a 3D raster
map:

```sh
i.hyper.atcorr lut=scene.lut \
    sza=35 vza=4 raa=95 \
    atmosphere=midsum aerosol=continental \
    aod=0.0,0.1,0.2,0.5 h2o=0.5,1.5,3.0,5.0 \
    wl_min=400 wl_max=2500 wl_step=10
```

The next command computes the lookup table and corrects a radiance cube using
scene values for AOD and water vapour:

```sh
i.hyper.atcorr input=scene_radiance output=scene_reflectance \
    lut=scene.lut sza=35 vza=4 raa=95 doy=180 \
    atmosphere=midsum aerosol=continental \
    aod_val=0.15 h2o_val=2.0
```

Atmospheric raster maps can be used instead of scene values:

```sh
i.hyper.atcorr input=scene_radiance output=scene_reflectance \
    sza=35 vza=4 raa=95 doy=180 \
    atmosphere=midsum aerosol=continental \
    aod_map=aod_550 h2o_map=water_vapour smooth=2
```

## SEE ALSO

*[i.atcorr](https://grass.osgeo.org/grass-stable/manuals/i.atcorr.html),
[i.hyper.metadata](i.hyper.metadata.md),
[i.atcorr2](https://github.com/YannChemin/i.atcorr2),
[i.hyper.atcorr reference implementation](https://github.com/YannChemin/i.hyper.atcorr)*

## REFERENCES

- Vermote, E.F., Tanre, D., Deuze, J.L., Herman, M. and Morcrette, J.J.
  (1997). Second simulation of the satellite signal in the solar spectrum,
  6S: An overview. *IEEE Transactions on Geoscience and Remote Sensing*,
  35(3), 675-686.
- Kotchenova, S.Y., Vermote, E.F., Matarrese, R. and Klemm, F.J. (2006).
  Validation of a vector version of the 6S radiative transfer code for
  atmospheric correction of satellite data. *Applied Optics*, 45(26),
  6762-6774.
- Thompson, D.R. et al. (2018). Optimal estimation for imaging spectrometer
  atmospheric correction. *Remote Sensing of Environment*, 216, 355-373.

## AUTHORS

Yann Chemin, Seilio Douar EI; Tomaz Zagar, Geodetic Institute of Slovenia
