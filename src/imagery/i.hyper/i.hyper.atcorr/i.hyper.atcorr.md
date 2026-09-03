## DESCRIPTION

*i.hyper.atcorr* performs atmospheric correction of a hyperspectral 3D
raster map. The input is calibrated top of atmosphere spectral radiance. The
output is unitless bottom of atmosphere surface reflectance.

The module uses the 6SV2.1 radiative transfer model to compute a lookup table
over aerosol optical depth (AOD) at 550 nm, column water vapour, and
wavelength. It converts radiance to top of atmosphere reflectance using the
acquisition day, solar zenith angle, and solar irradiance spectrum, then
interpolates the lookup table to invert surface reflectance.

The *lut* option writes the table computed by the current invocation. It is
output-only and is never read as correction input. A lookup table can be
written without correcting a raster. Correction requires both *input* and
*output*; *lut* may additionally save the table used by that correction.

Atmospheric conditions can be supplied as scene values with *aod_val* and
*h2o_val*, or as raster maps with *aod_map* and *h2o_map*. Raster map values
take precedence over scene values where they are not null. The atmospheric
maps can be smoothed before correction.

The module can estimate selected atmospheric quantities from suitable input
bands. It can also apply adjacency, terrain illumination, and surface
anisotropy corrections. Optional outputs include reflectance uncertainty, a
quality mask, and the directional area scattering factor (DASF).

## OPTIONS

The *aod* and *h2o* options define the lookup table axes. The default H2O grid
is `0.5,1.0,1.5,2.0,3.5,5.0` g/cm2. The scene fallback *h2o_val* defaults to
2.0 g/cm2. The wavelength axis is defined by *wl_min*, *wl_max*, and
*wl_step* in nanometres. The axes should cover input wavelengths and expected
atmospheric values.

The atmosphere can be represented by a standard profile selected with
*atmosphere*. The aerosol model is selected with *aerosol*.
`aerosol=desert` selects the complete background desert model (BDM), including
its optical properties and phase matrices. When `aerosol=custom` is used,
*mie_r*, *mie_sigma*, *mie_mr*, and *mie_mi* define a log-normal spherical
Mie aerosol.

The *altitude* option is sensor altitude in kilometres. Values less than or
equal to zero select ground mode. Values greater than zero and less than 100
select aircraft mode and use partial Rayleigh, aerosol, and gas columns
between target and sensor. Values greater than or equal to 100 select
satellite mode and use the full atmospheric column. The default is 1000 km.

Flag *-P* enables vector radiative transfer. The built-in aerosol choices
`none`, `continental`, `maritime`, `urban`, and `desert` use the complete
available polarization phase-matrix data. Combining *-P* with
`aerosol=custom` is rejected because custom Mie polarization is unsupported.
The vector solver propagates Stokes I, Q, and U internally so polarization
feeds back into Stokes I. The module uses the resulting Stokes-I path
reflectance but does not output Q or U.

Flags *-a*, *-w*, and *-z* estimate AOD, water vapour, and ozone from the
input map. Flag *-p* estimates surface pressure from the oxygen A band. Flag
*-e* performs a joint AOD and water vapour retrieval. These operations require
wavelength metadata and suitable input bands. The *dem* option instead uses
mean terrain elevation to set surface pressure for lookup table computation.
Image-based retrievals remain dependent on scene content, metadata, model
choices, and configured lookup table ranges; they are not a general
standalone replacement for ancillary atmospheric information.

The *slope* and *aspect* raster maps enable terrain illumination correction
and must be supplied together. The *sun_azimuth* option or supported scene
metadata supplies solar azimuth. Per-pixel view geometry can be given with
*view_zenith* for terrain path-length correction and with *view_zenith* and
*view_azimuth* for BRDF normalization.

The *brdf_fiso*, *brdf_fvol*, and *brdf_fgeo* raster maps enable nadir BRDF
adjusted reflectance normalization and must all be supplied. The
*mcd43_fiso*, *mcd43_fvol*, and *mcd43_fgeo* options provide spectral MCD43
kernel weights and must also be supplied together. All MCD43 raster and
comma-separated inputs must already have the product scale factor applied.
The module does not apply a 0.001 scale factor.

Flag *-u* computes reflectance uncertainty, written when *uncertainty* is
specified. Flag *-m* computes the bitmask written with *quality*. The quality
mask is an output product only and is not applied to mask or null the
corrected reflectance cube. Flag *-D* computes DASF and writes it with *dasf*.
Flag *-r* applies surface prior regularisation and requires the complete
reflectance cube to be held in memory.

## RADIATIVE TRANSFER

The lookup table stores four effective inversion coefficients at every grid
point: gas-weighted atmospheric path reflectance `R_atm`, total downward
transmittance `T_down`, gas-weighted total upward transmittance `T_up`, and
atmospheric spherical albedo `s_alb`.

`R_atm` is not gas-free path reflectance. Its aerosol and multiple-scattering
part and its Rayleigh part are weighted by their applicable gas
transmittances. Similarly, the stored upward coefficient is
`T_up_sca * T_gas,total / T_gas,down`, while the stored downward coefficient
is `T_down_sca * T_gas,down`. Their product therefore includes total gas
absorption over the complete Sun-surface-sensor path.

For a Lambertian surface, the inversion is

```text
rho_toa = pi * L * d2 / (E0 * cos(sza))
y = (rho_toa - R_atm) / (T_down * T_up)
rho_boa = y / (1 + s_alb * y)
```

where `L` is radiance per micrometre, `d2` is squared Earth-Sun distance, and
`E0` is solar spectral irradiance. The spherical-albedo denominator uses `y`,
not the unknown `rho_boa` on its right-hand side.

Automatic libRadtran/reptran spectral response function correction is
disabled and unsupported. Its gas parameterization cannot be multiplied into
the current 6SV effective coefficients consistently. Support remains pending
a mathematically consistent integration into `R_atm`, `T_down`, and `T_up`.

## NOTES

Radiometric metadata may declare spectral radiance per nanometre or per
micrometre. Per-nanometre values are multiplied by 1000; per-micrometre values
are unchanged, giving internal W m-2 sr-1 um-1. Missing radiometric units
produce a warning and are assumed to be per micrometre. Reflectance input and
other unsupported radiometric units are rejected.

Band centre and FWHM metadata may use `nm`, `um`, or `cm-1`. Nanometres are
divided by 1000 and micrometres are unchanged. Wavenumber centres are
converted as `wavelength_um = 10000 / wavenumber_cm-1`; wavenumber FWHM is
converted as `fwhm_um = 10000 * fwhm_cm-1 / wavenumber_cm-1^2`. Missing
wavelength units default to nm. Unsupported unit strings are rejected. The
module reads resolved metadata exclusively through `i.hyper.metadata`; input
maps must provide valid hyperspectral metadata.

Output and uncertainty metadata are derived from the input in one atomic
`i.hyper.metadata` operation. Each output receives a new dataset identifier,
one source-to-output history entry, and its local radiometry and atmospheric
correction settings. Failure to create valid output metadata aborts the module.

The module reads the following resolved input metadata. Product availability
refers to metadata written by *i.hyper.import*; "when present" means that the
field is conditional in the source product.

| Use or option | Resolved metadata key | Units or values | EnMAP | PRISMA | Tanager | Module fallback |
| --- | --- | --- | --- | --- | --- | --- |
| Band centres | `bands.wavelength` | `nm`, `um` (µm), or `cm-1` | Yes | Yes | Yes | LUT wavelength grid, with warning |
| Band FWHM | `bands.fwhm` | Same unit as band centres | Yes | Yes | Yes | 0 (unavailable) |
| Wavelength units | `wavelength_units` | `nm`, `um`, or `cm-1` | Yes | Yes | Yes | `nm` |
| Radiometric quantity | `radiometric_quantity` | Radiance or reflectance | Yes | Yes | Yes | Unset |
| Radiometric units | `radiometric_units` | W m-2 sr-1 nm-1 or W m-2 sr-1 µm-1 | Yes | Yes | Yes | W m-2 sr-1 µm-1, with warning |
| *sza* | `extended_metadata.geometry.sun_zenith_deg` | Degrees | Yes | Yes | Yes | Required |
| *vza* | `extended_metadata.geometry.view_zenith_deg` | Degrees | Yes | Yes | Yes | 0 |
| *raa* | `extended_metadata.geometry.relative_azimuth_deg` | Degrees | Yes | Yes | Yes | 0 |
| *sun_azimuth* | `extended_metadata.geometry.sun_azimuth_deg` | Degrees clockwise from north | Yes | Yes | Yes | 180 |
| *altitude* | `extended_metadata.geometry.sensor_altitude_m` | Metadata in m; option in km | When present | No | No | 1000 km |
| *doy* | `extended_metadata.acquisition.day_of_year` | Day index, 1-366 | Yes | Yes | Yes | 180 |
| *aod_val* | `extended_metadata.atmosphere.aod_550` | Unitless, at 550 nm | When present | No | Map mean when present | 0.1 |
| *h2o_val* | `extended_metadata.atmosphere.h2o_g_cm2` | g/cm2 | When present | No | Map mean when present | 2.0 g/cm2 |
| *ozone* | `extended_metadata.atmosphere.ozone_du` | Dobson units (DU) | When present | No | No | 300 DU |
| *atmosphere* | `extended_metadata.atmosphere.atmosphere_model` | `us62`, `midsum`, `midwin`, `tropical`, `subsum`, or `subwin` | No | When present | No | `us62` |
| *aerosol* | `extended_metadata.atmosphere.aerosol_model` | `none`, `continental`, `maritime`, `urban`, `desert`, or `custom` | No | No | No | `continental` |

For metadata-backed options, values are resolved in this order: command line
option, input map metadata, module fallback. Lookup table axes, flags, files,
and ancillary raster maps are not read from metadata.

The day-of-year range is 1 through 366, with a default of 180.
It is used for Earth-Sun distance. The solar and view angles must describe the
input acquisition geometry.

Values outside an AOD or water vapour lookup table axis are limited to its
nearest boundary. A finer table increases computation and memory use. The
default binary table, with 6 AOD points, 6 H2O points, and 211 wavelengths,
is 122448 bytes (about 120 KiB). The format size is
`20 + 4*(n_aod+n_h2o+n_wl) + 16*n_aod*n_h2o*n_wl` bytes.

The 2D ancillary raster maps are read in the current computational region.
Set the region to the horizontal extent and resolution of the input 3D raster
before running the module. Null radiance cells remain null. Bands with
round-trip transmittance below 0.10 are also written as null.

Final output reflectance is clipped to the interval from
-0.01 to 1.5, retaining the module's established range after all optional
processing.

The source-vendored *libsixsv* tree is compiled directly into the GRASS
module by both supported build descriptions. A separately installed
*libsixsv* shared library is not required. Building requires GRASS development
libraries, a C11 compiler, the math library, and OpenMP support. libRadtran is
not a supported module dependency while automatic SRF correction is disabled.

Surface prior regularisation, uncertainty calculation, DASF retrieval, and
some image-based retrievals need arrays for the complete scene. Memory use
therefore increases with the number of cells and bands.

## EXAMPLES

Compute and write a lookup table without correcting a 3D raster:

```sh
i.hyper.atcorr lut=scene.lut \
    sza=35 vza=4 raa=95 \
    atmosphere=midsum aerosol=continental \
    aod=0.0,0.1,0.2,0.5 h2o=0.5,1.0,1.5,2.0,3.5,5.0 \
    wl_min=400 wl_max=2500 wl_step=10
```

Compute a table in memory, optionally save it, and correct a radiance cube
using scene AOD and water vapour:

```sh
i.hyper.atcorr input=scene_radiance output=scene_reflectance \
    lut=scene_correction.lut sza=35 vza=4 raa=95 doy=180 \
    atmosphere=midsum aerosol=continental \
    aod_val=0.15 h2o_val=2.0
```

Use the BDM desert aerosol for a Saharan scene:

```sh
i.hyper.atcorr input=sahara_radiance output=sahara_reflectance \
    sza=28 vza=3 raa=110 doy=120 \
    atmosphere=tropical aerosol=desert \
    aod_val=0.35 h2o_val=1.0
```

Use atmospheric raster maps instead of scene values:

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
