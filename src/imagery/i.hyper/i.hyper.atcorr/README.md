<!-- markdownlint-disable MD013 MD040 MD060 MD046 MD024 -->

# i.hyper.atcorr

> **GitHub**: <https://github.com/yannchemin/i.hyper.atcorr>

GRASS GIS add-on for atmospheric correction of hyperspectral imagery using a
C port of the 6SV2.1 (Second Simulation of a Satellite Signal in the Solar
Spectrum) radiative transfer algorithm with OpenMP parallelisation.

---

## Overview

*i.hyper.atcorr* operates in two complementary modes:

| Mode | Trigger | Purpose |
|------|---------|---------|
| **LUT generation** | `lut=` | Compute and write a binary look-up table of atmospheric parameters over an [AOD × H₂O × wavelength] grid |
| **Cube correction** | `input=` and `output=` | Compute a LUT in memory and apply it to a 3D raster radiance cube, writing a surface (BOA) reflectance cube |

Both modes can be combined in a single invocation; the LUT is computed once
and used immediately for correction.

`lut=` is output-only: the module does not read an existing LUT. An `input=`
correction therefore requires `output=`; specifying `lut=` as well only saves
the LUT computed by that invocation.

---

## Physics

### Forward model (6SV)

For each (AOD, H₂O, λ) grid point the module stores four atmospheric
parameters:

| Symbol | Name |
|--------|------|
| **R_atm** | Gas-weighted effective atmospheric path reflectance |
| **T_down** | Total downward transmittance (direct + diffuse) |
| **T_up** | Gas-weighted effective total upward transmittance (direct + diffuse) |
| **s_alb** | Spherical albedo of the atmosphere |

The stored coefficients are arranged so that their product represents the
combined scattering and gas terms used by the inversion. In particular,
`R_atm` weights the aerosol/multiple-scattering and Rayleigh path components
by their applicable gas transmittances. The stored upward coefficient is
`T_up_sca × T_gas,total / T_gas,down`, while `T_down` contains
`T_down_sca × T_gas,down`; consequently `T_down × T_up` contains total gas
absorption over the complete Sun-surface-sensor path. These are effective
inversion coefficients, not gas-free scattering quantities.

### Inversion (BOA reflectance)

```
ρ_toa = (π × L × d²) / (E₀ × cos θₛ)
y     = (ρ_toa − R_atm) / (T_down × T_up)
ρ_boa = y / (1 + s_alb × y)
```

where *L* is TOA radiance in W/(m² sr µm), *E₀* is the Thuillier solar
irradiance (from 6SV2.1 tables), and *d²* is the squared Earth-Sun distance
for the acquisition day-of-year.

### Sensor altitude

`altitude=` is the sensor altitude in kilometres and selects three modes:

- `altitude <= 0`: ground sensor; no target-to-sensor atmospheric column
- `0 < altitude < 100`: aircraft sensor; uses partial Rayleigh, aerosol, and
  gas columns between the target and aircraft
- `altitude >= 100`: satellite sensor; uses the full atmospheric column

The default is 1000 km.

### Aerosols and vector radiative transfer

`aerosol=desert` uses the complete background desert model (BDM) optical and
phase-matrix tables rather than a continental proxy. With `-P`, the built-in
models (`none`, `continental`, `maritime`, `urban`, and `desert`) use their
full aerosol polarization data in the vector Stokes calculation. Combining
`-P` with `aerosol=custom` is rejected because the custom Mie model does not
provide a mathematically compatible polarized phase matrix.

Vector transfer propagates Stokes I, Q, and U internally so polarization can
feed back into Stokes I. The module consumes only the resulting Stokes-I
`R_atm`; neither corrected Q/U products nor Q/U arrays in the binary LUT are
written.

Automatic libRadtran/reptran SRF correction is disabled and unsupported. Its
gas parameterization is incompatible with direct multiplication into the
current 6SV effective coefficients. It must not be enabled until SRF effects
can be integrated consistently into `R_atm`, `T_down`, and `T_up`.

### Input units and metadata

Input must be calibrated spectral radiance. Metadata units per nanometre are
multiplied by 1000 to obtain W m⁻² sr⁻¹ µm⁻¹; per-micrometre units are used
unchanged. Missing radiometric units produce a warning and are assumed to be
per micrometre. Reflectance metadata is rejected, as is any radiometric unit
string not recognized as per-nanometre or per-micrometre radiance.

Band centres and FWHM may be declared in `nm`, `um`, or `cm-1`. Nanometres are
divided by 1000, micrometres are unchanged, and wavenumber centres are
converted with `λ[µm] = 10000 / ν[cm⁻¹]`. Wavenumber FWHM is converted with
`Δλ[µm] = 10000 Δν / ν²`. If wavelength units are absent they default to nm;
other unit strings are rejected. The history fallback accepts entries of the
form `Band N: WL nm` (with optional FWHM in nm).

Final output reflectance is clipped to [-0.01, 1.5] after optional processing,
retaining the module's established range. A
`quality=` mask is output-only and does not mask or null the corrected
reflectance cube.

---

## ISOFIT-Inspired Improvements

Six improvements inspired by the
[ISOFIT](https://github.com/isofit/isofit) framework are available as
optional flags and parameters. They can be combined freely; each defaults to
disabled for full backward compatibility.

### #1 — Per-pixel atmospheric maps + spatial smoothing

```
aod_map=<raster>   h2o_map=<raster>   smooth=<sigma_px>
```

Supply 2-D raster maps of AOD (at 550 nm) and/or column water vapour
(g/cm²) derived from Dark Target, MAIAC, or any retrieval product.
Per-pixel values replace the scalar `aod_val=` / `h2o_val=` fallbacks;
each pixel is corrected using trilinear LUT interpolation at its own
`(aod, h2o, λ)` point.

`smooth=` applies a **separable Gaussian filter** (σ in pixels) to the
maps before correction, suppressing retrieval noise while preserving large-
scale spatial gradients. Boundary pixels use edge-replication padding;
NaN/null pixels are excluded from the neighbourhood average.

### #2 — In-loop adjacency effect correction

```
adj_psf=<km>   [pixel_size=<m>]
```

Applies the **Vermote et al. (1997) adjacency correction** per band
immediately after algebraic inversion, before spectral regularisation.
The diffuse transmittance fraction carries signal from a spatially-
averaged environmental neighbourhood reflectance:

```
T_diff = clip(T_scat − T_dir, 0, T_scat)
r_env  = box_filter(r_boa, radius = adj_psf / pixel_size)
r_boa += T_diff × s_alb × (r_boa − r_env) / (1 − s_alb × r_env)
```

`T_dir` is the Beer-Lambert two-way direct transmittance computed from
Rayleigh + aerosol optical depths. `pixel_size=` is auto-detected from
the GRASS computational region if not given.

### #3 & #5 — Surface prior MAP regularisation (`-r` flag)

```
-r
```

After all bands have been inverted, blends each pixel's retrieved spectrum
with a **3-component Gaussian mixture surface prior** (vegetation, soil,
water) using diagonal-covariance MAP estimation:

```
r_map[b] = (r_obs[b] / σ_obs²[b]  +  r_prior[b] / σ_prior²[b])
           / (1/σ_obs²[b]  +  1/σ_prior²[b])
```

Each pixel is classified to the nearest component using VNIR bands
(0.40–1.00 µm). Prior means are hardcoded reference spectra interpolated to
the sensor wavelengths; prior variances scale as `(scale × mean)²`
(vegetation 15 %, soil 20 %, water 3 %). The `-r` flag requires loading the
full reflectance cube into memory (~400 MB for a 426-band Tanager scene).

### #4 — Per-band reflectance uncertainty (`-u` flag)

```
-u   [uncertainty=<output_raster3d>]
```

Computes per-pixel reflectance uncertainty (σ_rfl) for each band from two
propagated sources:

1. **Instrument noise**: NEDL estimated from the standard deviation of the
   darkest 5 % of radiance pixels → propagated as
   `σ_noise = π × NEDL × d² / (E₀ × cos θₛ × T_total)`

2. **AOD uncertainty**: LUT evaluated at `aod ± 0.04`; half the
   reflectance difference gives `σ_aod` per pixel.

Total: `σ_rfl = √(σ_noise² + σ_aod²)`

When `-r` is also enabled, the uncertainty cube feeds the MAP
regularisation as `σ_obs²`.

### #6 — Model discrepancy noise floor

When both `-u` and `-r` are active, a **per-band model discrepancy**
term is added in quadrature to σ_rfl before MAP regularisation.
It reflects systematic RT model errors:

- Baseline: 0.5 % (all bands)
- Gas absorption band edges (720, 760, 940, 1135, 1380, 1850 nm): +2 %
  Gaussian bump (σ = 30 nm)
- SWIR > 1500 nm: +1 % (aerosol model uncertainty)

This prevents over-regularisation in bands where the 6SV gas
parameterisation is least accurate.

---

## Hyperspectral-Native Features

Two additional features exploit the continuous 400–2500 nm sampling of
hyperspectral sensors and are only meaningful with 200+ bands.

### FlexBRDF — spectrally-varying NBAR

Standard NBAR applies a single scalar f_iso/f_vol/f_geo at every band.
**FlexBRDF** (Queally 2022; Garcia-Beltran 2024) disaggregates the 7-band
MCD43A1 kernel weights to the full hyperspectral grid:

1. Piecewise-linear interpolation between the 7 MODIS band centres
   {0.469, 0.555, 0.645, 0.858, 1.240, 1.640, 2.130} µm.
2. Optional **Tikhonov second-difference spectral smoothing** solves
   `(I + α²·D₂ᵀD₂)·x = f` in O(5n) via Cholesky band factorization,
   removing the piecewise kinks at anchor points.

```sh
i.hyper.atcorr -w -a \
    input=enmap_radiance output=enmap_nbar \
    lut=enmap.lut \
    sza=35 vza=4 raa=110 doy=160 \
    atmosphere=us62 aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.5 h2o=0.5,1.0,2.0,3.5 \
    aod_val=0.12 h2o_val=1.8 \
    sun_azimuth=155 view_zenith=enmap_vza view_azimuth=enmap_vaa \
    mcd43_fiso="0.112,0.117,0.095,0.243,0.155,0.118,0.085" \
    mcd43_fvol="0.045,0.040,0.038,0.131,0.038,0.022,0.014" \
    mcd43_fgeo="0.017,0.014,0.012,0.052,0.016,0.009,0.006" \
    mcd43_alpha=0.10 \
    wl_min=376 wl_max=2499 wl_step=5
```

Each of the three comma-separated 7-float strings gives MCD43A1 kernel
weights at the MODIS band centres in order B3, B4, B1, B2, B5, B6, B7.
Inputs must already be physically scaled; apply the MCD43 product scale
factor before passing either these values or the `brdf_f*` rasters. The
module does not apply a 0.001 scale factor. Per-pixel spatial amplitude rasters
(`brdf_fiso=`, `brdf_fvol=`, `brdf_fgeo=`) can be combined: the effective
weight at band z and pixel i is `f_iso_px(i) × fiso_wl(z) / fiso_wl(858 nm)`.
When only scene-mean scalar kernels are given, the per-pixel factor is 1.

### DASF — Directional Area Scattering Factor

**DASF** (Knyazikhin 2013 PNAS) retrieves a canopy structural parameter from
the 710–790 nm NIR plateau where canopy reflectance is linearly proportional
to leaf single-scattering albedo ω_L(λ):

```
ρ_boa(λ) ≈ DASF × ω_L(λ)
DASF = Σ[ρ(λ) × ω_L(λ)] / Σ[ω_L(λ)²]   (least-squares)
```

Leaf albedo ω_L(λ) is taken from a PROSPECT-D table (Féret et al. 2017,
Cab = 40 µg/cm²) at 5 nm steps.  The DASF raster is NaN for non-vegetation
pixels (NDVI < 0.2, derived from bands saved during correction) and clipped
to [0.01, 1.0].

```sh
i.hyper.atcorr -z -w -a -D \
    input=tanager_radiance output=tanager_refl \
    lut=tanager.lut \
    sza=30 vza=4 raa=100 doy=200 \
    atmosphere=midsum aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 h2o=0.5,1.5,3.0,5.0 \
    wl_min=376 wl_max=2499 wl_step=5 \
    dasf=tanager_dasf
```

Output: a 2-D FCELL raster `tanager_dasf`.  DASF ~ 0.9 for dense closed
forest; ~ 0.5–0.7 for open shrubland; NaN for bare soil, water, urban.

## Usage

**Image-based retrieval — which flags to activate per scene type**:

| Scene | Flags | Rationale |
|-------|-------|-----------|
| Saharan dust | `aerosol=desert -z dem=` | Use the BDM desert aerosol; no DDV over barren desert; O₃ and elevation matter |
| Amazon / tropical | `-z -w -a` | Dense forest = ideal DDV; ~4 g/cm² WVC gradient; low tropical O₃ |
| Urban temperate winter | `-z -a` | Variable O₃ (polar vortex); farmland DDV; dry winter air |
| Mediterranean coastal | `-w -a` | Land–sea H₂O gradient; coastal DDV; stable O₃ |
| Sub-arctic winter | `-z` | Polar O₃ enhancement; snow = no DDV; very dry |
| Boreal summer / mountain | `-z -w -a dem=` | All four: dense DDV + WVC gradient + variable O₃ + elevation |

### LUT generation only

```sh
i.hyper.atcorr \
    lut=kanpur.lut \
    sza=35.2 vza=4.1 raa=97 \
    atmosphere=midsum aerosol=continental ozone=310 \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 \
    h2o=1.0,2.0,3.5,5.0 \
    wl_min=376 wl_max=2499 wl_step=5
```

### Correction with scalar atmospheric state

```sh
i.hyper.atcorr \
    input=tanager_radiance output=tanager_refl \
    lut=tanager_correction.lut \
    sza=35.2 vza=4.1 raa=97 doy=45 \
    aod_val=0.18 h2o_val=3.5 \
    atmosphere=midsum aerosol=continental
```

### Full ISOFIT pipeline — all 6 improvements

```sh
i.hyper.atcorr -u -r \
    input=tanager_radiance output=tanager_refl \
    sza=35.2 vza=4.1 raa=97 doy=45 \
    aod_val=0.18 h2o_val=3.5 \
    atmosphere=midsum aerosol=continental \
    aod_map=maiac_aod h2o_map=mod05_wvc \
    smooth=3 \
    adj_psf=1.0 \
    uncertainty=tanager_refl_unc
```

Runs with:

- Per-pixel AOD from MAIAC, H₂O from MOD05, Gaussian-smoothed at σ=3 px
- Adjacency correction with 1 km PSF (auto pixel size from region)
- Surface prior MAP regularisation
- Uncertainty output in `tanager_refl_unc`

### Image-based retrieval example

This example derives selected atmospheric values from available image bands
and uses a DEM for surface pressure. It is not a standalone retrieval claim:
the result depends on suitable wavelength metadata, scene content, the DEM,
the selected atmospheric and aerosol models, and the configured LUT ranges.

```sh
i.hyper.atcorr -z -w -a \
    input=tanager_radiance output=tanager_refl \
    lut=tanager_auto.lut \
    sza=35.2 vza=4.1 raa=97 doy=45 \
    atmosphere=midsum aerosol=continental \
    dem=srtm_dem \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 \
    h2o=0.5,1.5,3.0,5.0 \
    wl_min=376 wl_max=2499 wl_step=5
```

- **`-z`** retrieves scene-mean O₃ (DU) from Chappuis absorption at 600 nm;
  replaces `ozone=` before the LUT is computed
- **`-w`** retrieves per-pixel WVC (g/cm²) from three H₂O absorption features
  (720, 940, 1135 nm) with FWHM power-law K scaling (α=0.78) and a per-pixel
  median consensus; used in place of `h2o_val=`
- **`-a`** retrieves per-pixel AOD at 550 nm from the MODIS DDV algorithm
  (470/660/860/2130 nm); non-DDV pixels receive the scene-mean AOD
- **`dem=`** computes ISA surface pressure from the mean DEM elevation and
  updates the LUT configuration before computation

---

## Options Reference

Metadata precedence is not a general rule for every option. For supported
scene scalar fields only, precedence is **CLI → input-map metadata → module
default**: `sza`, `vza`, `raa`, `sun_azimuth`, `altitude`, `ozone`, `aod_val`,
`h2o_val`, and `doy`. `sza` has no usable default and must come from the CLI or
metadata. Atmosphere and aerosol model names also have explicit metadata
fallbacks; LUT axes, files, flags, and ancillary raster options do not.

### I/O

| Option | Type | Description |
|--------|------|-------------|
| `input=` | R3 raster | TOA spectral radiance; metadata may declare per-nm or per-µm units |
| `output=` | R3 raster | BOA surface reflectance |
| `lut=` | file | Binary LUT output file; never read as correction input |

### Geometry

| Option | Default | Description |
|--------|---------|-------------|
| `sza=` | — | Solar zenith angle (°) |
| `vza=` | 0 | View zenith angle (°) |
| `raa=` | 0 | Relative azimuth angle (°) |
| `altitude=` | 1000 | Sensor altitude in km: <=0 ground, >0 and <100 aircraft, >=100 satellite |

### Atmosphere

| Option | Default | Description |
|--------|---------|-------------|
| `atmosphere=` | us62 | Standard atmosphere model |
| `aerosol=` | continental | Aerosol type: `none`, `continental`, `maritime`, `urban`, `desert`, `custom` |
| `ozone=` | 300 | Ozone column (Dobson units) |
| `mie_r=` | 0.10 | Custom Mie: log-normal mode radius [µm] (only when `aerosol=custom`) |
| `mie_sigma=` | 1.50 | Custom Mie: geometric std dev σ_g > 1 (only when `aerosol=custom`) |
| `mie_mr=` | 1.45 | Custom Mie: real refractive index at 550 nm (only when `aerosol=custom`) |
| `mie_mi=` | 0.005 | Custom Mie: imaginary refractive index at 550 nm (only when `aerosol=custom`) |

### LUT grid

| Option | Default | Description |
|--------|---------|-------------|
| `aod=` | 0.0,0.05,0.1,0.2,0.4,0.8 | AOD at 550 nm grid points |
| `h2o=` | 0.5,1.0,1.5,2.0,3.5,5.0 | H₂O grid points (g/cm²) |
| `wl_min=` | 400 | Minimum wavelength (nm) |
| `wl_max=` | 2500 | Maximum wavelength (nm) |
| `wl_step=` | 10 | Wavelength step (nm) |

### Correction

| Option | Default | Description |
|--------|---------|-------------|
| `doy=` | 180 | Day of year (Earth-Sun distance), range 1–366 |
| `aod_val=` | 0.1 | Scene-average AOD (scalar fallback) |
| `h2o_val=` | 2.0 | Scene-average H₂O g/cm² (scalar fallback) |

### ISOFIT improvements

| Option / Flag | Default | Description |
|---------------|---------|-------------|
| `aod_map=` | — | Per-pixel AOD raster (#1) |
| `h2o_map=` | — | Per-pixel H₂O raster (#1) |
| `smooth=` | 0 | Gaussian smoothing σ in pixels for atm maps (#1) |
| `adj_psf=` | 0 | Adjacency PSF radius km (0=off) (#2) |
| `pixel_size=` | 0 | Pixel size m (0=auto from region) (#2) |
| `-r` | off | Surface prior MAP regularisation (#3/#5/#6) |
| `-u` | off | Compute per-band uncertainty (#4) |
| `uncertainty=` | — | Output uncertainty 3D raster (#4) |

### Image-based Retrieval

These flags retrieve atmospheric state directly from the input radiance cube,
when the required bands and wavelength metadata are available. `-z` and
`dem=` update the LUT configuration before it is computed; `-w` and `-a`
provide per-pixel arrays used during the correction step. They do not make
every scene independent of ancillary data or atmospheric assumptions.

| Option / Flag | Description |
|---------------|-------------|
| `-z` | Retrieve scene-mean O₃ (DU) from Chappuis band depth at 600 nm; requires bands near 540, 600, 680 nm |
| `-w` | Retrieve per-pixel WVC (g/cm²) from three H₂O features (720/940/1135 nm) with per-pixel median consensus; FWHM scaling applied automatically |
| `-a` | Retrieve per-pixel AOD at 550 nm from MODIS DDV algorithm; requires bands near 470, 660, 860, 2130 nm |
| `-m quality=` | Write a 2-D cloud/shadow/water/snow bitmask; output-only and not applied to the corrected reflectance cube |
| `dem=` | ISA surface pressure from mean elevation of a DEM raster; replaces default 1013.25 hPa |

### Polarization

| Option / Flag | Default | Description |
|---------------|---------|-------------|
| `-P` | off | Vector Stokes-I feedback using full polarization tables for built-in aerosols; no Q/U output; incompatible with `aerosol=custom` |

### FlexBRDF — spectrally-varying NBAR

| Option | Default | Description |
|--------|---------|-------------|
| `mcd43_fiso=` | — | 7 comma-separated, already-scaled f_iso kernel weights at MODIS band centres (B3,B4,B1,B2,B5,B6,B7) |
| `mcd43_fvol=` | — | 7 comma-separated f_vol kernel weights (must accompany `mcd43_fiso=` and `mcd43_fgeo=`) |
| `mcd43_fgeo=` | — | 7 comma-separated f_geo kernel weights |
| `mcd43_alpha=` | 0.10 | Tikhonov second-difference regularization strength (0 = off; 0.05–0.20 typical) |

The module does not apply the MCD43 0.001 product scale factor. Values passed
through all `mcd43_f*` and `brdf_f*` inputs must already be scaled.

### DASF retrieval

| Option / Flag | Default | Description |
|---------------|---------|-------------|
| `-D` | off | Retrieve DASF (canopy structural scattering factor) inline with correction; requires `output=` and `dasf=` |
| `dasf=` | — | Output 2-D FCELL raster name for the DASF product; NaN for non-vegetation (NDVI < 0.2) |

---

## Architecture

The 6SV implementation is a source-vendored copy of
**[libsixsv/](libsixsv/)**, imported from
[YannChemin/libsixsv](https://github.com/yannchemin/libsixsv) with git subtree.
The module Makefile and CMake target compile those C sources directly into the
GRASS module; a separately installed `libsixsv` shared library is not a build
or runtime dependency. The build requires GRASS development libraries, a C11
compiler, the math library, and OpenMP support. libRadtran is not a supported
module dependency because automatic SRF correction is disabled.

---

## LUT file format

Host-endian binary (little-endian on x86):

```
magic     uint32   0x4C555400  ("LUT\0")
version   uint32   1
n_aod     int32
n_h2o     int32
n_wl      int32
aod[n_aod]                     float32
h2o[n_h2o]                     float32
wl [n_wl]                      float32  (micrometres)
R_atm [n_aod × n_h2o × n_wl]  float32
T_down[n_aod × n_h2o × n_wl]  float32
T_up  [n_aod × n_h2o × n_wl]  float32
s_alb [n_aod × n_h2o × n_wl]  float32
```

C order: wavelength index varies fastest.
The file size is `20 + 4(n_aod + n_h2o + n_wl) +
16(n_aod n_h2o n_wl)` bytes. The default 6 AOD × 6 H₂O × 211 wavelength grid
is 122,448 bytes (about 120 KiB), not multiple megabytes.

---

## References

- Vermote, E.F., Tanré, D., Deuzé, J.L., Herman, M. and Morcrette, J.J.
  (1997): Second simulation of the satellite signal in the solar spectrum,
  6S: An overview. *IEEE Trans. Geosci. Remote Sens.*, 35(3), 675–686.
- Kotchenova, S.Y., Vermote, E.F., Matarrese, R. and Klemm, F.J. (2006):
  Validation of a vector version of the 6S radiative transfer code for
  atmospheric correction of satellite data. *Applied Optics*, 45(26),
  6762–6778.
- Thompson, D.R. et al. (2018): Optimal estimation for imaging
  spectrometer atmospheric correction. *Remote Sensing of Environment*,
  216, 355–373. (ISOFIT)
- Vermote, E.F., El Saleous, N., Justice, C.O., Kaufman, Y.J.,
  Privette, J.L., Remer, L., Roger, J.C. and Tanré, D. (1997):
  Atmospheric correction of visible to middle-infrared EOS-MODIS data over
  land surfaces: Background, operational algorithm and validation.
  *J. Geophys. Res. Atmos.*, 102(D14), 17131–17141. (adjacency correction)
- Queally, N. et al. (2022): FlexBRDF: A flexible BRDF correction for
  grouped processing of airborne imaging spectroscopy flightlines.
  *Journal of Geophysical Research: Biogeosciences*, 127, e2021JG006545.
- Garcia-Beltran, A. et al. (2024): HABA: A new hyperspectral albedo-based
  algorithm for estimating plant area index. *Remote Sensing*, 16, 1405.
- Knyazikhin, Y. et al. (2013): Hyperspectral remote sensing of foliar
  nitrogen content. *Proceedings of the National Academy of Sciences*,
  110(3), E185–E192. (DASF spectral invariance)
- Féret, J.B. et al. (2017): PROSPECT-D: Towards modeling leaf optical
  properties through a complete lifecycle. *Remote Sensing of Environment*,
  193, 204–215. (PROSPECT-D leaf albedo)

## Related repositories

| Repository | Relationship | Description |
|---|---|---|
| [libsixsv](https://github.com/yannchemin/libsixsv) | **Upstream source** | Source-vendored 6SV2.1 implementation; no separately installed library is required by this module |

## Subtree dependency

[libsixsv/](libsixsv/) is vendored from
<https://github.com/YannChemin/libsixsv> via **git subtree**.
To pull upstream changes:

    git subtree pull --prefix src/imagery/i.hyper/i.hyper.atcorr/libsixsv \
        https://github.com/YannChemin/libsixsv.git main --squash

## Authors

Yann Chemin, Seilio Douar EI; Tomaž Žagar and Alen Mangafić, Geodetic Institute
of Slovenia.
