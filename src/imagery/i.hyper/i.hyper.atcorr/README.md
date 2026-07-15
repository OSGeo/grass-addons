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
| **LUT generation** | `lut=` | Compute a binary look-up table of atmospheric parameters over an [AOD × H₂O × wavelength] grid |
| **Cube correction** | `input=` / `output=` | Apply the LUT to a Raster3D radiance cube, writing a surface (BOA) reflectance cube |

Both modes can be combined in a single invocation; the LUT is computed once
and used immediately for correction.

---

## Physics

### Forward model (6SV)

For each (AOD, H₂O, λ) grid point the module stores four atmospheric
parameters:

| Symbol | Name |
|--------|------|
| **R_atm** | Atmospheric path reflectance |
| **T_down** | Total downward transmittance (direct + diffuse) |
| **T_up** | Total upward transmittance (direct + diffuse) |
| **s_alb** | Spherical albedo of the atmosphere |

### Inversion (BOA reflectance)

```
ρ_toa = (π × L × d²) / (E₀ × cos θₛ)
ρ_boa = (ρ_toa − R_atm) / (T_down × T_up × (1 + s_alb × ρ_boa))
```

where *L* is TOA radiance in W/(m² sr µm), *E₀* is the Thuillier solar
irradiance (from 6SV2.1 tables), and *d²* is the squared Earth-Sun distance
for the acquisition day-of-year.

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
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

Each of the three comma-separated 7-float strings gives MCD43A1 kernel
weights (scale factor 0.001 already applied) at the MODIS band centres in
order B3, B4, B1, B2, B5, B6, B7.  Per-pixel spatial amplitude rasters
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
    wl_min=0.376 wl_max=2.499 wl_step=0.005 \
    dasf=tanager_dasf
```

Output: a 2-D FCELL raster `tanager_dasf`.  DASF ~ 0.9 for dense closed
forest; ~ 0.5–0.7 for open shrubland; NaN for bare soil, water, urban.

---

## Installation

Two build modes are available. Choose based on whether GRASS GIS is present.

---

### Mode 1 — GRASS GIS module (default `make`)

**Prerequisites**

- GRASS GIS 8.x source tree (default: `$HOME/dev/grass`)
- GCC with OpenMP (`-fopenmp`)

**Build**

The RT physics library ([libsixsv](https://github.com/yannchemin/libsixsv))
must be installed first:

```sh
cd ~/dev/libsixsv
make MODULE_TOPDIR=$HOME/dev/grass
sudo make install MODULE_TOPDIR=$HOME/dev/grass
```

Then build and install the module:

```sh
cd ~/dev/i.hyper.atcorr
make
sudo cp dist.*/bin/i.hyper.atcorr        /usr/local/grass85/bin/
sudo cp dist.*/lib/libgrass_sixsv.8.6.so /usr/local/grass85/lib/
```

---

### Mode 2 — Standalone Debian binary (`make DEBIAN_BUILD=1`)

Runs entirely without GRASS GIS.  Reads GeoTIFF and HDF5 cubes directly via
**[libras3d](https://github.com/yannchemin/libras3d)**.

**Prerequisites** (Debian trixie packages):

```sh
sudo dpkg -i libras3d_0.1.0-1_amd64.deb \
              libras3d-dev_0.1.0-1_amd64.deb \
              libsixsv1_1.0.0-1_amd64.deb \
              libsixsv-dev_1.0.0-1_amd64.deb
```

**Build and install**

```sh
cd ~/dev/i.hyper.atcorr
make DEBIAN_BUILD=1
sudo make DEBIAN_BUILD=1 install   # → /usr/local/bin/i.hyper.atcorr
```

**Run** (no GRASS environment needed):

```sh
export RAS3D_PATH=/path/to/input/data
export RAS3D_OUTDIR=/path/to/output

i.hyper.atcorr \
    input=scene.tiff \
    output=scene_boa \
    sza=35.2 doy=221
```

Key environment variables when running standalone:

| Variable | Purpose |
|---|---|
| `RAS3D_PATH` | Directory searched for input cubes by name |
| `RAS3D_OUTDIR` | Directory for output GeoTIFF files |
| `RAS3D_HDF5_DATASET` | Override HDF5 dataset path (e.g. for Tanager/Wyvern) |
| `RAS3D_VERBOSE` | Verbosity level: 0 quiet, 1 normal, 2 verbose |

---

## Usage

**Image-based retrieval — which flags to activate per scene type**:

| Scene | Flags | Rationale |
|-------|-------|-----------|
| Saharan dust | `-z dem=` | No DDV (barren desert); dry uniform H₂O; O₃ and elevation matter |
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
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

### Correction with scalar atmospheric state

```sh
i.hyper.atcorr \
    input=tanager_radiance output=tanager_refl \
    lut=kanpur.lut \
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

### Fully standalone — all atmospheric state from the image

No external ancillary products required.  A single command retrieves O₃,
per-pixel H₂O, per-pixel AOD, and surface pressure from the image, then
generates the LUT and applies the correction.

```sh
i.hyper.atcorr -z -w -a \
    input=tanager_radiance output=tanager_refl \
    lut=tanager_auto.lut \
    sza=35.2 vza=4.1 raa=97 doy=45 \
    atmosphere=midsum aerosol=continental \
    dem=srtm_dem \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 \
    h2o=0.5,1.5,3.0,5.0 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
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

### I/O

| Option | Type | Description |
|--------|------|-------------|
| `input=` | R3 raster | TOA radiance W/(m² sr µm) |
| `output=` | R3 raster | BOA surface reflectance |
| `lut=` | file | Binary LUT output file |

### Geometry

| Option | Default | Description |
|--------|---------|-------------|
| `sza=` | — | Solar zenith angle (°) |
| `vza=` | 0 | View zenith angle (°) |
| `raa=` | 0 | Relative azimuth angle (°) |
| `altitude=` | 1000 | Sensor altitude in km (>900 = satellite) |

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
| `h2o=` | 0.5,1.0,2.0,3.5,5.0 | H₂O grid points (g/cm²) |
| `wl_min=` | 0.40 | Minimum wavelength (µm) |
| `wl_max=` | 2.50 | Maximum wavelength (µm) |
| `wl_step=` | 0.01 | Wavelength step (µm) |

### Correction

| Option | Default | Description |
|--------|---------|-------------|
| `doy=` | 180 | Day of year (Earth-Sun distance) |
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
| `uncertainty=` | — | Output uncertainty Raster3D (#4) |

### Image-based Retrieval

These flags retrieve atmospheric state directly from the input radiance cube,
eliminating the need for co-located ancillary products.  `-z` and `dem=`
update the LUT configuration before it is computed; `-w` and `-a` provide
per-pixel arrays used during the correction step.

| Option / Flag | Description |
|---------------|-------------|
| `-z` | Retrieve scene-mean O₃ (DU) from Chappuis band depth at 600 nm; requires bands near 540, 600, 680 nm |
| `-w` | Retrieve per-pixel WVC (g/cm²) from three H₂O features (720/940/1135 nm) with per-pixel median consensus; FWHM scaling applied automatically |
| `-a` | Retrieve per-pixel AOD at 550 nm from MODIS DDV algorithm; requires bands near 470, 660, 860, 2130 nm |
| `dem=` | ISA surface pressure from mean elevation of a DEM raster; replaces default 1013.25 hPa |

### FlexBRDF — spectrally-varying NBAR

| Option | Default | Description |
|--------|---------|-------------|
| `mcd43_fiso=` | — | 7 comma-separated f_iso kernel weights at MODIS band centres (B3,B4,B1,B2,B5,B6,B7); scale factor 0.001 applied |
| `mcd43_fvol=` | — | 7 comma-separated f_vol kernel weights (must accompany `mcd43_fiso=` and `mcd43_fgeo=`) |
| `mcd43_fgeo=` | — | 7 comma-separated f_geo kernel weights |
| `mcd43_alpha=` | 0.10 | Tikhonov second-difference regularization strength (0 = off; 0.05–0.20 typical) |

### DASF retrieval

| Option / Flag | Default | Description |
|---------------|---------|-------------|
| `-D` | off | Retrieve DASF (canopy structural scattering factor) inline with correction; requires `output=` and `dasf=` |
| `dasf=` | — | Output 2-D FCELL raster name for the DASF product; NaN for non-vegetation (NDVI < 0.2) |

---

## Architecture

The RT physics live in the **[libsixsv](https://github.com/yannchemin/libsixsv)**
sibling repository (`~/dev/libsixsv`), compiled into `libgrass_sixsv.so` (GRASS
mode) or `libsixsv.so` (Debian standalone mode).  This add-on repo contains only
the GRASS/ras3d module interface (`main.c`) and the Python bindings.

When built with `DEBIAN_BUILD=1`, the four GRASS headers are replaced by a
single `<ras3d/ras3d.h>` include (detected via `HAVE_RAS3D` guard).  The
**[libras3d](https://github.com/yannchemin/libras3d)** library provides
drop-in implementations of `Rast3d_*`, `G_*`, and `Rast_*` symbols backed by
libtiff/libgeotiff (GeoTIFF) and libhdf5 (HDF5).

```
~/dev/libsixsv/                              (github.com/yannchemin/libsixsv)
├── src/
│   ├── lut.c            OpenMP LUT computation (AOD outer loop)
│   │                    + atcorr_lut_interp_pixel() trilinear interp
│   ├── discom.c         6SV scattering at 20 reference wavelengths (SOS)
│   ├── interp.c         Log-log wavelength interpolation
│   ├── gas_abs.c        Curtis-Godson gas transmittance
│   ├── aerosol.c        Aerosol mixture initialisation
│   ├── atmosphere.c     Standard atmosphere models
│   ├── srf_conv.c       SRF gas correction via libRadtran reptran fine
│   ├── spatial.c        Separable Gaussian + box filters          [#1]
│   ├── adjacency.c      Vermote 1997 adjacency correction         [#2]
│   ├── surface_model.c  3-component surface prior + MAP           [#3,#5,#6]
│   ├── uncertainty.c    Noise + AOD-perturbation uncertainty      [#4]
│   ├── spectral_brdf.c  MCD43 disaggregation + Tikhonov smoother [FlexBRDF]
│   ├── retrieve.c       Image-based retrieval (H2O/AOD/O3/DASF)
│   └── rt.c / scatra.c / ... (6SV RT solver, ported from Fortran)
├── include/
│   ├── atcorr.h         Public API (LutConfig, LutArrays, all exports)
│   ├── spatial.h        [#1]
│   ├── adjacency.h      [#2]
│   ├── surface_model.h  [#3,#5,#6]
│   ├── uncertainty.h    [#4]
│   ├── spectral_brdf.h  FlexBRDF (mcd43_disaggregate, spectral_smooth_tikhonov)
│   └── retrieve.h       Retrieval API (H2O, AOD, O3, DASF)
└── Makefile             builds libgrass_sixsv.so; hardcodes -fopenmp -lgomp
                         (GRASS Platform.make sets OPENMP_LIB= empty unless
                         GRASS itself was configured with --with-openmp)

~/dev/i.hyper.atcorr/                       (github.com/yannchemin/i.hyper.atcorr)
├── main.c               GRASS module interface, correct_raster3d()
└── python/
    └── atcorr.py        ctypes bindings (LutConfig, compute_lut, lut_slice,
                         atcorr_lut_interp_pixel, apply_srf_correction)
```

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
Typical size: ~4 MB for 6 AOD × 5 H₂O × 211 wavelengths.

---

## Python bindings

`libgrass_sixsv.so` is importable from Python via ctypes (`python/atcorr.py`):

```python
from atcorr import LutConfig, compute_lut, lut_slice, apply_srf_correction

cfg = LutConfig(sza=35.2, vza=4.1, raa=97, ...)
lut = compute_lut(cfg)          # returns LutArrays with numpy arrays
Rs, Tds, Tus, ss = lut_slice(cfg, lut, aod_val=0.18, h2o_val=3.5)
lut = apply_srf_correction(cfg, lut, fwhm_um=band_fwhm, threshold_nm=5.0)
```

### FlexBRDF from Python

```python
import numpy as np
from atcorr import mcd43_disaggregate, spectral_smooth_tikhonov

# Sensor wavelengths (e.g. EnMAP, 420 bands 0.40–2.45 µm)
wl = np.linspace(0.40, 2.45, 420, dtype=np.float32)

# MCD43A1 kernel weights (scale factor 0.001 already applied)
fiso_7 = [0.112, 0.117, 0.095, 0.243, 0.155, 0.118, 0.085]
fvol_7 = [0.045, 0.040, 0.038, 0.131, 0.038, 0.022, 0.014]
fgeo_7 = [0.017, 0.014, 0.012, 0.052, 0.016, 0.009, 0.006]

# Disaggregate to sensor grid with Tikhonov smoothing (alpha=0.10)
fiso_wl, fvol_wl, fgeo_wl = mcd43_disaggregate(
    fiso_7, fvol_7, fgeo_7, wl, alpha=0.10
)
# fiso_wl, fvol_wl, fgeo_wl are float32 arrays of shape (420,)

# Apply spectral smoothing to any signal independently
from atcorr import spectral_smooth_tikhonov
smoothed = spectral_smooth_tikhonov(some_spectrum, alpha=0.05)
```

### DASF from Python

```python
import numpy as np
from atcorr import retrieve_dasf

# Suppose `refl_cube` is [n_bands, npix] BOA reflectance from the GRASS module
# Select the 710-790 nm bands from the full cube:
nir_mask  = (wl >= 0.710) & (wl <= 0.790)
wl_nir    = wl[nir_mask]                   # e.g. 17 bands for 5 nm step sensor
refl_nir  = refl_cube[nir_mask, :]         # shape (17, npix)

dasf = retrieve_dasf(refl_nir, wl_nir)    # float32 [npix]; NaN for bad pixels

# Leaf albedo decomposition: recover effective leaf spectrum
# (vectorised for all pixels at once)
from atcorr import mcd43_disaggregate
# (use the same wl_nir grid for leaf_albedo_nir — internal PROSPECT-D table)
# For visualization, compute pixel-mean DASF and divide into mean reflectance:
valid = np.isfinite(dasf) & (dasf > 0.05)
mean_dasf   = float(np.nanmean(dasf[valid]))
leaf_albedo = refl_cube[:, valid].mean(axis=1) / mean_dasf
```

---

## C API

`libgrass_sixsv.so` can be linked directly from C or C++.  Include the
relevant header from `~/dev/libsixsv/include/` and link with `-lgrass_sixsv`.

### FlexBRDF from C

```c
#include "libsixsv/include/spectral_brdf.h"
#include <stdlib.h>

/* Sensor wavelength grid (n_wl bands) */
int n_wl = 420;
float *wl = ...;   /* µm, 0.40–2.45 */

/* MCD43A1 kernel weights (7 bands, scale factor 0.001 applied) */
float fiso_7[7] = {0.112f, 0.117f, 0.095f, 0.243f, 0.155f, 0.118f, 0.085f};
float fvol_7[7] = {0.045f, 0.040f, 0.038f, 0.131f, 0.038f, 0.022f, 0.014f};
float fgeo_7[7] = {0.017f, 0.014f, 0.012f, 0.052f, 0.016f, 0.009f, 0.006f};

float *fiso_wl = malloc(n_wl * sizeof(float));
float *fvol_wl = malloc(n_wl * sizeof(float));
float *fgeo_wl = malloc(n_wl * sizeof(float));

/* Disaggregate with Tikhonov smoothing (alpha=0.10) */
mcd43_disaggregate(fiso_7, fvol_7, fgeo_7,
                   wl, n_wl, 0.10f,
                   fiso_wl, fvol_wl, fgeo_wl);

/* Optional: smooth any other spectrum independently */
spectral_smooth_tikhonov(some_spectrum, n_wl, 0.05f);  /* in-place */

/* NBAR ratio at band z:
 *   scale_iso = fiso_wl[z] / fiso_wl[i858]
 *   f_obs_wl  = (fiso_px + fvol_px * K_RT + fgeo_px * K_LS)
 *               × scale_iso / scale_iso_obs ... (see brdf.c)
 */
free(fiso_wl); free(fvol_wl); free(fgeo_wl);
```

### DASF from C

```c
#include "libsixsv/include/retrieve.h"
#include <math.h>

/* After atmospheric correction, select the 710-790 nm bands */
/* refl[b * npix + i] = band b of pixel i (band-major layout)  */
int n_dasf = 17;   /* bands within 710-790 nm */
int npix   = nrows * ncols;
float *refl_nir  = ...;   /* [n_dasf × npix], band-major          */
float *wl_nir    = ...;   /* n_dasf wavelengths [µm] in 710-790   */
float *dasf      = malloc(npix * sizeof(float));

retrieve_dasf(refl_nir, wl_nir, n_dasf, npix, dasf);

/* dasf[i] ∈ [0.01, 1.0], NaN for non-vegetation / bad pixels */
for (int i = 0; i < npix; i++) {
    if (!isnan(dasf[i]))
        /* ... process vegetation pixel ... */;
}
free(dasf);
```

---

## Validation

The test suite contains **178 tests** across 6 files, all passing:

| File | Tests | Scope |
|------|-------|-------|
| `testsuite/test_fortran_compat.py` | 32 | Fortran 6SV2.1 ↔ C function agreement |
| `testsuite/test_lut.py` | 47 | LUT generation, inversion, spectral/geometry/H₂O behaviour |
| `testsuite/test_solar.py` | 15 | Solar irradiance spectrum + Earth-Sun distance |
| `testsuite/test_retrievals.py` | 47 | H₂O triplet, consensus, OE inversion |
| `testsuite/test_spectral_brdf.py` | 20 | FlexBRDF (MCD43), Tikhonov smoother, DASF |
| `testsuite/test_grass_module.py` | 17 | End-to-end GRASS module integration |

### Fortran 6SV2.1 compatibility (`test_fortran_compat.py`, 32 tests)

Cross-checks every C function in `libgrass_sixsv.so` against the original
Fortran 77 subroutines compiled from `~/dev/6sV2.1/`.

| Subroutine | Function tested | Tests | Tolerance | Actual agreement |
|---|---|---|---|---|
| CHAND | `sixs_chand()` – Chandrasekhar Rayleigh reflectance | 4 geometries | rtol=1×10⁻⁵ | ~7×10⁻⁸ (float32 limit) |
| ODRAYL | `sixs_odrayl()` – Rayleigh optical depth (Edlén 1966) | 6 wavelengths (VIS/NIR/SWIR) | rtol=5×10⁻³ | ~2×10⁻⁷ |
| ODRAYL monotone | λ⁻⁴ spectral law: τ_blue >> τ_NIR >> τ_SWIR | 2 ratio checks | physics | confirmed |
| VARSOL × d² ≈ 1 | `sixs_earth_sun_dist2()` – Earth-Sun distance | 4 DOYs | rtol=5×10⁻³ | <0.07% |
| SOLIRR / E0 on-grid | `sixs_E0()` – Thuillier solar irradiance | 4 wavelengths | rtol=1×10⁻³ | 0–3 ULP |
| SOLIRR / E0 off-grid | `sixs_E0()` – linear vs nearest-neighbour interp | 1 wavelength | rtol=1×10⁻³ | 0.035% |
| CSALBR | `sixs_csalbr()` – Rayleigh spherical albedo | 3 τ values | rtol=1×10⁻⁵ | ~9×10⁻⁸ (float32 limit) |
| GAUSS | `sixs_gauss()` – Gauss-Legendre quadrature | n=4, n=8, n=16; weight sums, symmetry, nodes | rtol=1×10⁻⁵ | Exact float32 |

Minor intentional differences:
- `sixs_E0()` uses linear interpolation for off-grid wavelengths; Fortran SOLIRR uses nearest-neighbour — both agree to 0.035% (smooth solar spectrum).
- `sixs_earth_sun_dist2()` returns d² (< 1 at perihelion); Fortran VARSOL returns 1/d² (> 1 at perihelion) — the product ≈ 1.0 within 0.07%, confirming complementary conventions.
- Solar table float32 literals produce 0–3 ULP differences between gfortran and the C compiler at parse time — not a bug.

**Build and run:**

```sh
# Compile 6SV2.1 Fortran objects (first time only)
cd ~/dev/6sV2.1
gfortran -O -ffixed-line-length-132 -c CHAND.f ODRAYL.f VARSOL.f SOLIRR.f CSALBR.f GAUSS.f US62.f

# Run all 32 Fortran compatibility tests
cd ~/dev/i.hyper.atcorr
grass --tmp-project XY --exec python3 testsuite/test_fortran_compat.py
```

The Fortran driver (`testsuite/test_6sv_compat.f90`) is compiled automatically
by the Python test suite when the Fortran objects are present.

### Run full test suite

```sh
cd ~/dev/i.hyper.atcorr
grass --tmp-project XY --exec python3 -m pytest testsuite/ -v
```

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
| [libsixsv](https://github.com/yannchemin/libsixsv) | **Upstream dependency** | 6SV2.1 RT physics library; provides LUT computation, per-pixel inversion, BRDF models, retrievals |
| [libras3d](https://github.com/yannchemin/libras3d) | **Upstream dependency — Debian only** | Standalone GRASS raster3d replacement; enables `DEBIAN_BUILD=1` without a GRASS installation |

## License

This is free and unencumbered software released into the public domain.  
See <https://unlicense.org> for the full text.

## Authors

i.hyper.smac project / Yann Chemin.
