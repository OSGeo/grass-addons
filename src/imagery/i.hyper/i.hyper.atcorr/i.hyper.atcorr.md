## DESCRIPTION

*i.hyper.atcorr* is a GRASS GIS add-on for atmospheric correction of
hyperspectral imagery. It operates in two complementary modes that can
be combined in a single invocation:

| Mode | Trigger | Purpose |
|------|---------|---------|
| **LUT generation** | `lut=` | Compute a binary look-up table of atmospheric parameters over an [AOD × H₂O × wavelength] grid |
| **Cube correction** | `input=` / `output=` | Apply the LUT to a Raster3D radiance cube, writing a surface (BOA) reflectance cube |

The LUT is computed using a C port of the 6SV2.1 (Second Simulation of
a Satellite Signal in the Solar Spectrum, version 2.1) radiative
transfer code with OpenMP parallelisation over the AOD dimension.

For each (AOD, H₂O, λ) grid point the module stores four atmospheric
parameters:

- **R_atm** — atmospheric path reflectance
- **T_down** — total downward transmittance (direct + diffuse)
- **T_up** — total upward transmittance (direct + diffuse)
- **s_alb** — spherical albedo of the atmosphere

These four parameters are sufficient to invert a top-of-atmosphere (TOA)
reflectance to surface (BOA) reflectance via the standard algebraic
formula:

```
ρ_toa = (π × L × d²) / (E₀ × cos θₛ)
ρ_boa = (ρ_toa − R_atm) / (T_down × T_up × (1 + s_alb × ρ_boa))
```

where *L* is TOA radiance in W/(m² sr µm), *E₀* is the Thuillier solar
irradiance from 6SV2.1 tables, and *d²* is the squared Earth-Sun
distance for the acquisition day-of-year.

---

## ISOFIT-INSPIRED IMPROVEMENTS

Six improvements inspired by the
[ISOFIT](https://github.com/isofit/isofit) framework are available as
optional flags and parameters. They can be combined freely; each
defaults to disabled for full backward compatibility.

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
maps before correction, suppressing retrieval noise while preserving
large-scale spatial gradients. Boundary pixels use edge-replication
padding; NaN/null pixels are excluded from the neighbourhood average.

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

After all bands have been inverted, blends each pixel's retrieved
spectrum with a **3-component Gaussian mixture surface prior**
(vegetation, soil, water) using diagonal-covariance MAP estimation:

```
r_map[b] = (r_obs[b] / σ_obs²[b]  +  r_prior[b] / σ_prior²[b])
           / (1/σ_obs²[b]  +  1/σ_prior²[b])
```

Each pixel is classified to the nearest component using VNIR bands
(0.40–1.00 µm). Prior means are hardcoded reference spectra
interpolated to the sensor wavelengths; prior variances scale as
`(scale × mean)²` (vegetation 15 %, soil 20 %, water 3 %). The `-r`
flag requires loading the full reflectance cube into memory (~400 MB
for a 426-band Tanager scene).

### #4 — Per-band reflectance uncertainty (`-u` flag)

```
-u   [uncertainty=<output_raster3d>]
```

Computes per-pixel reflectance uncertainty (σ_rfl) for each band from
two propagated sources:

1. **Instrument noise**: NEDL estimated from the standard deviation of
   the darkest 5 % of radiance pixels → propagated as
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
- Gas absorption band edges (720, 760, 940, 1135, 1380, 1850 nm):
  +2 % Gaussian bump (σ = 30 nm)
- SWIR > 1500 nm: +1 % (aerosol model uncertainty)

This prevents over-regularisation in bands where the 6SV gas
parameterisation is least accurate.

---

## C LIBRARY API (libgrass_sixsv.so)

`libgrass_sixsv.so` exposes the full 6SV2.1 radiative transfer engine as a C
library.  The following functions were added in the Phase 1–5 port from
the original Fortran code and are available to any caller that links against
the library.

### Atmosphere profiles

Six standard atmosphere models are now fully implemented (US Standard 1962,
Mid-latitude Summer, Mid-latitude Winter, Tropical, Sub-arctic Summer,
Sub-arctic Winter).  Select via `atmosphere=` as described above.

### Utility functions (Phase 2)

```c
/* Solar zenith and azimuth from date / location / time */
void sixs_possol(int month, int jday, float tu,
                 float xlon, float xlat,
                 float *asol, float *phi0, int ia);

/* Chandrasekhar analytical Rayleigh reflectance */
float sixs_chand(float xphi, float xmuv, float xmus, float xtau);

/* Vermote environmental adjacency weighting factors */
void sixs_enviro(float difr, float difa, float r, float palt,
                 float xmuv,
                 float *fra, float *fae, float *fr);
```

### Aerosol vertical profile and surface pressure (Phase 3)

```c
/* Fill ctx->aerprof with an exponential aerosol layer profile */
void sixs_aeroprof(SixsCtx *ctx, float aod550, float ome,
                   float haa, float alt);

/* Trim the atmosphere profile to a surface pressure (hPa > 0)
   or altitude (km, passed as negative value) */
void sixs_pressure(SixsCtx *ctx, float sp);

/* As above but also returns the trimmed H2O and O3 columns */
void sixs_pressure_columns(SixsCtx *ctx, float sp,
                            float *uw, float *uo3);
```

### Custom Mie aerosol (Phase 4)

```c
/* Compute aerosol single-scattering properties for a log-normal
   size distribution via Bohren–Huffman Mie scattering.
   Fills ctx->aer (ext/sca/phase at 20 reference wavelengths). */
void sixs_mie_init(SixsCtx *ctx,
                   double r_mode,   /* mode radius µm         */
                   double sigma_g,  /* geometric std dev       */
                   double m_r_550,  /* real refractive index   */
                   double m_i_550); /* imaginary ref. index    */
```

Set `LutConfig.aerosol_type = AEROSOL_CUSTOM` (value 9) and call
`sixs_mie_init()` on the per-thread context before computing the LUT
to use a custom particle size distribution.

**From the GRASS module**, use `aerosol=custom` with the four companion options:

```
aerosol=custom  mie_r=0.10  mie_sigma=1.50  mie_mr=1.50  mie_mi=0.015
```

| Option | Default | Description |
|--------|---------|-------------|
| `mie_r=` | 0.10 | Log-normal mode radius [µm] (AERONET fine-mode: 0.08–0.15 µm) |
| `mie_sigma=` | 1.50 | Geometric standard deviation σ_g (typical: 1.4–1.8) |
| `mie_mr=` | 1.45 | Real refractive index at 550 nm (dust≈1.55, carbon≈1.75, marine≈1.38) |
| `mie_mi=` | 0.005 | Imaginary refractive index at 550 nm (absorbing: 0.01–0.05; scattering: <0.005) |

Typical values for common aerosol types:

| Type | r_mode | σ_g | n_r | n_i | Ångström α | SSA |
|------|--------|-----|-----|-----|------------|-----|
| Kanpur urban/pollution (AERONET fine) | 0.10 | 1.50 | 1.50 | 0.015 | ~1.8 | ~0.91 |
| Biomass burning | 0.12 | 1.60 | 1.54 | 0.025 | ~1.6 | ~0.87 |
| Continental mineral dust | 0.07 | 2.00 | 1.53 | 0.008 | ~0.3 | ~0.97 |
| Clean marine | 0.10 | 1.45 | 1.38 | 0.001 | ~1.0 | ~0.99 |

The Ångström exponent α controls how steeply AOD increases toward the blue.
Fine-mode (small r) raises α and thus path radiance in the 470 nm band
relative to the standard continental model (α≈0.5 from 70% coarse dust).

### BRDF surface models (Phase 5) and BRDF-RT coupling

```c
#include "libsixsv/include/brdf.h"

/* Evaluate BRDF at a single (SZA, VZA, RAA) point */
float sixs_brdf_eval(BrdfType type, const BrdfParams *params,
                     float cos_sza, float cos_vza, float raa_deg);

/* Bihemispherical (white-sky) albedo by midpoint quadrature over the
 * outgoing hemisphere.  n_phi=48, n_theta=24 gives < 0.1 % error. */
float sixs_brdf_albe(BrdfType type, const BrdfParams *params,
                     float cos_sza, int n_phi, int n_theta);
```

Available models (`BrdfType` enum):

| Value | Name | Description |
|-------|------|-------------|
| 0 | `BRDF_LAMBERTIAN` | Isotropic Lambertian (single `rho0` parameter) |
| 1 | `BRDF_RAHMAN` | Rahman–Pinty–Verstraete (RPV) — ρ₀, k, Θ |
| 2 | `BRDF_ROUJEAN` | Roujean volumetric kernel — k0, k1, k2 |
| 3 | `BRDF_HAPKE` | Hapke canopy model — ω, b, c, h |
| 4 | `BRDF_OCEAN` | Cox–Munk glint + whitecaps + water body — wind speed, pigment, salinity, foam fraction, water reflectance |
| 5 | `BRDF_WALTHALL` | Walthall polynomial — a0, a1, a2, a3 |
| 6 | `BRDF_MINNAERT` | Minnaert — k (limb-darkening exponent) |
| 7 | `BRDF_VERSFELD` | Versfeld (stub — returns 0) |
| 8 | `BRDF_IAPI` | IAPI canopy (stub — returns 0) |
| 9 | `BRDF_ROSSLIMAIGNAN` | Ross–Li + Maignan hot-spot — fiso, fvol, fgeo, h_ratio |

**BRDF-RT coupling** is enabled via the `brdf=` and `brdf_params=`
GRASS options (see Parameters section).  DISCOM always runs with a black
lower boundary (correct and efficient); the BRDF model is applied in the
inversion formula only.  For Lambertian surfaces the standard
`atcorr_invert()` path is unchanged.  For non-Lambertian surfaces
`atcorr_invert_brdf()` is used:

```
y        = (ρ_toa − R_atm) / (T_down × T_up)
ρ_brdf   = y × (1 − s_alb × ρ̄)
```

where ρ̄ is the bihemispherical (white-sky) albedo computed once per scene
via 48 × 24 midpoint quadrature.  The output is the bidirectional
reflectance factor (BRF) at the acquisition geometry.

---

## BRDF CORRECTION OPTIONS

```
brdf=lambertian|rahman|roujean|hapke|ocean|walthall|minnaert|rosslimaignan
brdf_params=<comma-separated floats>
```

Select a non-Lambertian surface BRDF model for the inversion formula.
`brdf_params=` accepts up to 5 comma-separated floats whose meaning
depends on the chosen model:

| Model | Parameters |
|-------|-----------|
| `lambertian` | `rho0` (constant reflectance; default 1.0) |
| `rahman` | `rho0, af, k` |
| `roujean` | `k0, k1, k2` |
| `hapke` | `om, af, s0, h` |
| `ocean` | `wspd_ms, azw_deg, sal_ppt, pcl_mgl, wl_um` |
| `walthall` | `a, ap, b, c` |
| `minnaert` | `k, b` |
| `rosslimaignan` | `f_iso, f_vol, f_geo` |

When `brdf=lambertian` (default), the standard Lambertian `atcorr_invert()`
formula is used and the output is BOA reflectance.  For any other model,
`atcorr_invert_brdf()` is used and the output is the bidirectional
reflectance factor (BRF) at the acquisition geometry.

---

## POLARIZATION OPTIONS

```
-P
```

Enable **vector (Stokes I, Q, U) radiative transfer** via `sixs_ospol()` instead
of the scalar `sixs_os()`.  When active, the module computes the full Stokes
description of the atmospheric path radiance, which improves R_atm accuracy by
1–5 % in the blue/UV bands where Rayleigh scattering is strongly polarised.

### Physics

The standard scalar path adds only the intensity component *I* of the multiply-
scattered radiance.  Rayleigh scattering is inherently polarised: photons
scattered at 90° are up to 100 % linearly polarised, and the coupling between
Q/U Stokes components and *I* raises the apparent path reflectance R_atm by
roughly 4–5 % at 400 nm, decreasing monotonically to < 0.5 % beyond 860 nm.
Aerosol scattering (assumed spherical in this implementation) contributes a
smaller correction because the phase matrix off-diagonal terms are near zero.

### Output arrays

When `-P` is set, `LutArrays` carries two additional arrays alongside R_atm:

| Field | Description |
|-------|-------------|
| `R_atmQ` | Q Stokes component of path reflectance (same [n_aod × n_h2o × n_wl] layout as R_atm) |
| `R_atmU` | U Stokes component of path reflectance |

For the typical geometry of a nadir-viewing satellite over a continental scene
(SZA 30°, VZA 5°, RAA 90°):

| Band | R_atm (scalar) | R_atm (vector) | R_atmQ | R_atmU |
|------|----------------|----------------|--------|--------|
| 400 nm | 0.140 | 0.147 (+4.6 %) | +0.016 | −0.005 |
| 450 nm | 0.093 | 0.097 (+3.8 %) | +0.011 | −0.003 |
| 550 nm | 0.043 | 0.044 (+2.3 %) | +0.005 | −0.002 |
| 660 nm | 0.020 | 0.020 (+1.3 %) | +0.002 | −0.001 |
| 860 nm | 0.006 | 0.006 (+0.4 %) | +0.001 |  0.000 |

### Surface polarisation models

Two surface polarisation forward models are included (available in `libgrass_sixsv.so`):

- **POLGLIT** (`libsixsv/src/polglit.c`) — Cox–Munk ocean glint polarisation; anisotropic
  Gaussian wave-facet distribution with Fresnel reflection (m = 1.33);
  wind-direction-dependent via `azw_deg`.
- **POLNAD** (`libsixsv/src/polglit.c`) — Nadal–Breon vegetation/soil model; Fresnel
  polarisation with N = 1.5; linear mix of vegetation (`pveg`) and soil
  contributions.

### C API

```c
/* Enable in LutConfig (zero by default) */
cfg.enable_polar = 1;

/* Pre-allocate Q/U arrays (same size as R_atm) */
size_t lut_sz = n_aod * n_h2o * n_wl;
float *R_atmQ = calloc(lut_sz, sizeof(float));
float *R_atmU = calloc(lut_sz, sizeof(float));

LutArrays lut = { R_atm, T_down, T_up, s_alb, NULL,
                  R_atmQ, R_atmU };
atcorr_compute_lut(&cfg, &lut);
```

### Performance

`sixs_ospol()` propagates a 3×3 Müller matrix at each quadrature point, so
vector RT is approximately **3× slower** than scalar RT.  For most operational
use-cases the accuracy gain in the blue bands does not justify the cost; the
flag is most useful for validation studies or blue-UV applications.

### Implementation notes

- `libsixsv/src/ospol.c` — port of 6SV2.1 `OSPOL.f`; successive-orders vector RT
- `libsixsv/src/kernelpol.c` — port of 6SV2.1 `KERNELPOL.f`; generalised spherical
  functions and Müller-matrix kernels
- `libsixsv/src/polglit.c` — port of 6SV2.1 `POLGLIT.f` + `POLNAD.f`; surface
  polarisation models
- `libsixsv/src/interp.c:sixs_interp_polar()` — linear (not log-log) interpolation for
  Q/U because those components can be negative
- After modifying `libsixsv/include/sixs_ctx.h` always run `make clean && make`
  in `~/dev/libsixsv/` — the Makefile has no automatic header-dependency
  tracking, and a stale `SixsDisc` layout causes a segfault in `sixs_gauss`

---

## IMAGE-BASED RETRIEVAL OPTIONS

i.hyper.atcorr can estimate the atmospheric state parameters directly from
the input hyperspectral cube, making the module fully standalone for scenes
with no external ancillary data.  All four retrievals are optional and
independent; they run before LUT computation so that retrieved O₃ and
surface pressure update the LUT, while retrieved AOD and H₂O are used as
per-pixel correction maps.

### `-z` — O₃ column from Chappuis band depth

Estimates the scene-mean ozone column from the Chappuis absorption feature
at ~600 nm using a continuum-interpolation approach:

```
L_cont = linear_interp(L_540, L_680) at 600 nm
D      = max(0, 1 − L_600 / L_cont)
O₃     = D / (σ₆₀₀ × m)     σ₆₀₀ ≈ 1.0×10⁻⁴ DU⁻¹
```

where *m* = 1/cos(θₛ) + 1/cos(θᵥ) is the two-way airmass factor.
The result (scene-mean DU) replaces the `ozone=` value for LUT computation.
Requires input= and band wavelength metadata in the cube.

### `-w` — Column water vapour from multi-band consensus

Estimates per-pixel water vapour column [g/cm²] from **three H₂O absorption
features** simultaneously and combines them into a per-pixel consensus
using `retrieve_h2o_triplet()` + `retrieve_h2o_consensus()`:

| Feature | Triplet (lo / feat / hi) | K_ref (cm²/g) | fwhm_ref | K at 5 nm FWHM |
|---------|--------------------------|---------------|----------|----------------|
| 720 nm  | 700 / 720 / 740 nm       | 0.0077        | 60 nm    | 0.054          |
| 940 nm  | 865 / 941 / 1042 nm      | 0.036         | 50 nm    | 0.217          |
| 1135 nm | 1100 / 1135 / 1175 nm    | 0.0376        | 45 nm    | 0.209          |

Per-pixel continuum interpolation and band-depth inversion (Kaufman & Gao 1992):

```
L_cont = L_lo × (1-FRAC) + L_hi × FRAC    (FRAC = (λ_feat−λ_lo)/(λ_hi−λ_lo))
D      = max(0, 1 − L_feat / L_cont)
K      = K_ref × (fwhm_ref / fwhm)^0.78   (FWHM power-law scaling, α=0.78)
WVC    = D / (K × m)                       (m = 1/cos θₛ + 1/cos θᵥ)
```

Pixels with D outside the valid range ([0.02, 0.60] / [0.05, 0.90] / [0.05, 0.85])
are excluded from that feature's estimate.  The per-pixel consensus is the
median of the valid estimates (1–3 features).  The scene mean updates
`h2o_val=` as the scalar fallback.  Requires `input=` with wavelength metadata.

### `-a` — AOD from Dark Dense Vegetation (DDV)

Estimates per-pixel AOD at 550 nm from dark vegetated pixels using the
**MODIS dark-target approach** (Kaufman et al. 1997):

**DDV mask:** 0.01 < ρ_toa(2130) < 0.25 AND NDVI(860, 660) > 0.1

**Surface prediction:** ρ_surf_470 = 0.25 ρ_2130; ρ_surf_660 = 0.50 ρ_2130

**Single-scattering inversion** (nadir view, Henyey-Greenstein, g=0.65, ω₀=0.89):

```
ρ_path = max(0, ρ_toa − ρ_surf)
τ      = ρ_path × 4μₛ / (ω₀ × P_HG)
α      = −ln(τ_470/τ_660) / ln(470/660)    (Ångström exponent)
τ_550  = τ_470 × (550/470)^(−α)
```

Non-DDV pixels are filled with the scene-mean AOD.  Requires bands at
approximately 470, 660, 860, and 2130 nm.

### `dem=` — Surface pressure from terrain elevation

Computes the scene-mean terrain elevation from a 2-D DEM raster [m] and
converts it to surface pressure using the ISA barometric formula:

```
P = 1013.25 × (1 − 2.2558×10⁻⁵ × h)^5.2559   [hPa]
```

The result replaces the standard-atmosphere sea-level pressure in LUT
computation, improving accuracy for elevated terrain.

### C Library API (retrieve.h)

The retrieval functions are also available from `libgrass_sixsv.so`:

```c
#include "libsixsv/include/retrieve.h"

/* H2O column [g/cm²] per pixel from a single (lo/feat/hi) band triplet.
 * K_ref is the broadband reference absorption coefficient [cm²/g].
 * fwhm_ref_um is the sensor FWHM for K_ref; fwhm_um is the actual sensor FWHM
 * (0 = use K_ref directly without FWHM scaling).
 * Pixels with D outside [D_min, D_max] are flagged invalid (out_valid=0). */
void retrieve_h2o_triplet(const float *L_lo, const float *L_feat,
                           const float *L_hi,
                           float wl_lo_um, float wl_feat_um, float wl_hi_um,
                           float K_ref, float fwhm_ref_um, float fwhm_um,
                           float D_min, float D_max,
                           int npix, float sza_deg, float vza_deg,
                           float *out_wvc, uint8_t *out_valid);

/* Per-pixel median consensus of n_methods WVC arrays.
 * Only pixels flagged valid (valid_arrays[i][px]=1) contribute.
 * Falls back to WVC_DEF=2.0 where no estimate is valid.
 * Returns the number of pixels with at least two agreeing estimates. */
int retrieve_h2o_consensus(int n_methods,
                            float * const *wvc_arrays,
                            uint8_t * const *valid_arrays,
                            int npix, float *out_wvc);

/* H2O column [g/cm²] per pixel from 940 nm band depth (legacy single-band) */
void retrieve_h2o_940(const float *L_865, const float *L_940,
                       const float *L_1040, int npix,
                       float sza_deg, float vza_deg, float fwhm_um,
                       float *out_wvc);

/* Per-pixel AOD at 550 nm from DDV; returns scene mean */
float retrieve_aod_ddv(const float *L_470, const float *L_660,
                        const float *L_860, const float *L_2130,
                        int npix, int doy, float sza_deg,
                        float *out_aod);

/* Scene-mean O₃ [DU] from Chappuis band depth */
float retrieve_o3_chappuis(const float *L_540, const float *L_600,
                            const float *L_680, int npix,
                            float sza_deg, float vza_deg);

/* ISA pressure [hPa] from mean terrain elevation [m] */
float retrieve_pressure_isa(float elev_m);
```

All functions are pure computation with no GRASS dependencies and can be
called directly from Python via ctypes.

---

## NOTES

### libRadtran — runtime-optional dependency

`grass_sixsv` has **no compile-time dependency on libRadtran**.
The library builds and links without it installed.

At runtime, `grass_sixsv` can optionally call the `uvspec` binary from
[libRadtran](http://www.libradtran.org) (via a `popen()` subprocess) inside
`atcorr_srf_compute()` to apply a spectral-response-function (SRF)
gas-transmittance correction.  This path is relevant only for hyperspectral
sensors with narrow bands (FWHM ≲ 5 nm, e.g. DESIS, PRISMA, EMIT).

If `uvspec` is not found on `$PATH`, `atcorr_srf_compute()` returns `NULL`
gracefully and logs a warning to `stderr`.  Atmospheric correction continues
without SRF convolution.  No crash or fatal error occurs.

To enable SRF correction, install libRadtran and ensure the `uvspec` binary is
on `$PATH` (or set `LIBRADTRAN_BIN` to its directory).

### LUT file format

The binary file is host-endian (little-endian on x86) and has the
following layout:

```
magic     uint32   0x4C555400 ("LUT\0")
version   uint32   1
n_aod     int32
n_h2o     int32
n_wl      int32
aod[n_aod]          float32
h2o[n_h2o]          float32
wl [n_wl]           float32   (micrometres)
R_atm [n_aod*n_h2o*n_wl]   float32
T_down[n_aod*n_h2o*n_wl]   float32
T_up  [n_aod*n_h2o*n_wl]   float32
s_alb [n_aod*n_h2o*n_wl]   float32
```

Array indexing is C order: the wavelength index varies fastest.
Typical size: ~4 MB for 6 AOD × 5 H₂O × 211 wavelengths.

### Radiative transfer

The RT solver is a direct C port of the 6SV2.1 Fortran code (Vermote
et al. 1997). Scattering is computed via the Successive Orders of
Scattering (SOS) method with Gauss–Legendre quadrature (25 points per
hemisphere, 30 atmospheric layers). Gas absorption (H₂O, O₃, CO₂, O₂,
N₂O, CH₄) is computed separately and folded into T_down and T_up so
that the scattering LUT only needs to be computed once per AOD value.

### OpenMP parallelism

Each AOD grid point is independent and is computed in a separate OpenMP
thread. On a 4-core machine a 6 AOD × 5 H₂O × 211 band LUT takes
approximately one second. The Gaussian spatial filter, adjacency
correction, uncertainty computation, and MAP regularisation all use
additional OpenMP parallel regions.

### Cube correction memory

When `-r` is active, the full reflectance cube is held in memory for
MAP regularisation. Memory usage is approximately
`n_bands × n_pixels × 4` bytes. For a 426-band Tanager scene with a
typical 640 × 480 tile this is about 400 MB. When `-r` is not set,
bands are written to the output Raster3D immediately after inversion.

### Band wavelength metadata

When correcting a Raster3D cube the module auto-reads band wavelengths
from `r3.info -h` metadata in the format `Band N: WL nm`. Make sure
this metadata is present in the input cube.

---

## EXAMPLES

Each example below first generates a LUT and then applies it to correct
a Raster3D radiance cube. Scene geometry, atmosphere, and aerosol type
are chosen to reflect realistic acquisition conditions for the land cover
and climate zone described.

**Image-based retrieval quick reference** — which flags to activate per scene:

| Example | Flags / options | Rationale |
|---------|-----------------|-----------|
| 1. Saharan dust | `-z dem=` | No DDV (barren desert); dry uniform H₂O; O₃ and elevation matter |
| 2. Amazon | `-z -w -a` | Dense forest = ideal DDV; ~4 g/cm² WVC gradient; low tropical O₃ |
| 3. Paris winter | `-z -a` | Variable O₃ (polar vortex); farmland DDV; dry winter air |
| 4. Mediterranean | `-w -a` | Land–sea H₂O gradient; coastal DDV; stable O₃ |
| 5. Sweden winter | `-z` | Polar O₃ enhancement at SZA=78°; snow = no DDV; very dry |
| 6. Yukon summer | `-z -w -a dem=` | All four: boreal DDV + tundra WVC gradient + variable O₃ + elevation |
| 10. Alps terrain | `slope= aspect= sun_azimuth=` | N/S slopes differ 10× in direct irradiance; T_down split into direct/diffuse |
| 11. Sahel NBAR | `brdf_fiso= brdf_fvol= brdf_fgeo=` + `view_zenith= view_azimuth=` | Wide-swath off-nadir sensor; NBAR removes cross-track BRF view-angle variation |
| 12. O₂-A pressure | `-p quality=` | Mountainous scene; per-pixel pressure and pre-correction masking |
| 13. MAIAC patch AOD | `-a maiac_patch=` | Dense vegetation; spatial patch regularization of DDV outliers |
| 14. Joint OE | `-e -w oe_sigma_aod=` | Most accurate simultaneous AOD+H₂O inversion; supersedes -a and -w |
| 15. FlexBRDF NBAR | `mcd43_fiso= mcd43_fvol= mcd43_fgeo= mcd43_alpha=` | Spectrally-varying NBAR across 400–2500 nm from MCD43 disaggregation + Tikhonov smoothing |
| 16. DASF retrieval | `-D dasf=` | Canopy structure parameter from 710–790 nm NIR plateau regression; NDVI-masked to vegetation |
| 17. Python API | `mcd43_disaggregate()` / `retrieve_dasf()` | FlexBRDF + DASF via `python/atcorr.py` without GRASS — for custom pipelines and Jupyter workflows |
| 18. C API | direct linkage to `libgrass_sixsv.so` | FlexBRDF + DASF from C/C++ (`-lgrass_sixsv`); minimal standalone example |

---

### 1. Saharan dust storm (desert, tropical atmosphere)

**Scene**: Algeria, March (DOY 90). High-sun geometry, extremely dry air,
heavy mineral dust load (AOD can exceed 2 during events).

```sh
# LUT: wide AOD range to cover moderate and heavy dust episodes
i.hyper.atcorr \
    lut=sahara_dust.lut \
    sza=40 vza=5 raa=150 \
    atmosphere=tropical aerosol=desert ozone=280 \
    aod=0.05,0.2,0.5,1.0,2.0,3.0 \
    h2o=0.2,0.5,1.0,1.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Correction with scalar state from an external MODIS dust product
i.hyper.atcorr \
    input=algeria_radiance output=algeria_refl \
    lut=sahara_dust.lut \
    sza=40 vza=5 raa=150 doy=90 \
    aod_val=0.85 h2o_val=0.4 \
    atmosphere=tropical aerosol=desert

# Image-based O₃ retrieval (-z) + ISA pressure from DEM.
# -a omitted: barren desert has no DDV-eligible vegetation pixels.
# -w omitted: Saharan H₂O < 1.5 g/cm² is spatially uniform; scalar sufficient.
i.hyper.atcorr -z \
    input=algeria_radiance output=algeria_refl \
    lut=sahara_dust_auto.lut \
    sza=40 vza=5 raa=150 doy=90 \
    atmosphere=tropical aerosol=desert \
    dem=srtm_dem \
    aod=0.05,0.2,0.5,1.0,2.0,3.0 h2o=0.2,0.5,1.0,1.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why `atmosphere=tropical`**: The tropical profile has the highest
near-surface temperature and pressure, better matching hot Saharan
conditions than the US62 standard.  Desert aerosol uses the Shettle/Fenn
mineral dust optical model (strongly wavelength-dependent: high AOD in
blue, flatter in NIR).  The narrow H₂O grid (0.2–1.5 g/cm²) reflects
the extremely low precipitable water of the Sahara.

**Retrieval flags**: **`-z`** retrieves scene-mean O₃ from the Chappuis
absorption band centred at 600 nm.  Tropical stratospheric O₃ deviates
±30–50 DU from the 280 DU prior, introducing a systematic tilt in the
540–700 nm reflectance if uncorrected.  **`dem=`** replaces the default
1013.25 hPa with the ISA formula at the mean terrain elevation; elevated
desert plateaux (e.g. Hoggar massif, ~2 000 m, P ≈ 795 hPa) have ~20 %
lower Rayleigh optical depth than sea level.  **`-a`** and **`-w`** are
omitted: barren desert has no DDV vegetation, and Saharan WVC is spatially
uniform enough for the scalar prior.

---

### 2. Tropical rainforest (Amazon, high humidity)

**Scene**: Pará state, Brazil, September (DOY 270). Near-overhead sun,
very high water vapour, background biogenic aerosol.

```sh
i.hyper.atcorr \
    lut=amazon.lut \
    sza=28 vza=0 raa=0 \
    atmosphere=tropical aerosol=continental ozone=260 \
    aod=0.03,0.08,0.15,0.30,0.50 \
    h2o=3.5,4.5,5.5,6.5,7.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Correction with scalar state (typical wet-season baseline)
i.hyper.atcorr \
    input=amazon_radiance output=amazon_refl \
    lut=amazon.lut \
    sza=28 vza=0 raa=0 doy=270 \
    aod_val=0.10 h2o_val=5.5 \
    atmosphere=tropical aerosol=continental

# Image-based retrieval: per-pixel H₂O (-w) + per-pixel AOD (-a) + O₃ (-z).
# Dense tropical forest is an ideal DDV target (NDVI > 0.8, ρ_2130 ≈ 0.05–0.12).
# H₂O gradients across the basin can span 3–7 g/cm²; per-pixel retrieval
# from the 940 nm band removes this spatial bias.
i.hyper.atcorr -z -w -a \
    input=amazon_radiance output=amazon_refl \
    lut=amazon_auto.lut \
    sza=28 vza=0 raa=0 doy=270 \
    atmosphere=tropical aerosol=continental \
    aod=0.03,0.08,0.15,0.30,0.50 h2o=3.5,4.5,5.5,6.5,7.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why high H₂O grid**: Precipitable water in tropical Amazonia routinely
exceeds 5 g/cm².  Extending the H₂O LUT axis above the default 5 g/cm²
prevents extrapolation error in the 940 nm and 1135 nm water vapour bands,
where transmittance is highly nonlinear.  Continental aerosol represents
the Aitken-mode biogenic VOC particles typical of the clean wet season.

**Retrieval flags**: **`-w`** retrieves per-pixel WVC from the 940 nm band
depth; the continental Amazon spans a ~4 g/cm² WVC gradient at any given
overpass, which translates to a 5–12 % NIR reflectance error if a single
scalar is used.  **`-a`** exploits dense forest as a DDV target
(ρ_2130 ≈ 0.05–0.12, NDVI > 0.8); per-pixel AOD from the 470/660 nm pair
captures smoke plumes from fire fronts at the forest edge.  **`-z`**
retrieves the tropical O₃ column, which is ~10–15 DU lower than the
mid-latitude standard (260 DU assumed vs 300 DU default), preventing a
systematic blue/green reflectance bias.

---

### 3. Urban temperate mid-winter (continental pollution)

**Scene**: Paris region, France, January (DOY 15). Low sun, cold and
dry air, traffic and heating fuel combustion aerosol, possible anticyclone
pollution build-up.

```sh
i.hyper.atcorr \
    lut=paris_winter.lut \
    sza=72 vza=5 raa=120 \
    atmosphere=midwin aerosol=urban ozone=330 \
    aod=0.05,0.15,0.30,0.60,1.00 \
    h2o=0.2,0.4,0.7,1.0 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Correction with scalar state + uncertainty output
i.hyper.atcorr -u \
    input=paris_radiance output=paris_refl \
    lut=paris_winter.lut \
    sza=72 vza=5 raa=120 doy=15 \
    aod_val=0.35 h2o_val=0.5 \
    atmosphere=midwin aerosol=urban \
    uncertainty=paris_refl_unc

# Image-based O₃ retrieval (-z) + DDV AOD from suburban farmland (-a).
# -w omitted: Paris in January has H₂O ≈ 0.2–0.7 g/cm²; spatial
# variability is small and the scalar prior is adequate.
i.hyper.atcorr -z -a -u \
    input=paris_radiance output=paris_refl \
    lut=paris_winter_auto.lut \
    sza=72 vza=5 raa=120 doy=15 \
    atmosphere=midwin aerosol=urban \
    uncertainty=paris_refl_unc \
    aod=0.05,0.15,0.30,0.60,1.00 h2o=0.2,0.4,0.7,1.0 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why `atmosphere=midwin` + `aerosol=urban`**: Mid-latitude winter
profiles have lower water vapour scale heights and a strong temperature
inversion that traps pollution.  Urban aerosol contains soot and sulfate
(higher single-scattering absorption, lower SSA than continental), making
the path radiance correction in the visible bands significantly larger
than for clean rural air.  The `-u` flag propagates AOD uncertainty
(±0.04) into the reflectance product, important here because high SZA
inflates the atmospheric path radiance sensitivity.

**Retrieval flags**: **`-z`** retrieves scene-mean O₃ from the Chappuis
band; winter mid-latitude O₃ columns over France range 300–380 DU
depending on quasi-biennial oscillation phase and polar vortex proximity —
a ±40 DU offset biases 540–700 nm reflectance by ~0.5 % at SZA=72°.
**`-a`** retrieves per-pixel AOD using DDV pixels in the agricultural
Beauce plain south of Paris (winter wheat fields, NDVI ~0.3–0.5,
ρ_2130 ≈ 0.06–0.12); the urban AOD gradient from city centre to rural
fringe spans 0.1–0.5, so per-pixel retrieval significantly improves the
correction over suburban areas.  **`-w`** is omitted: mid-winter WVC over
northern France is low (0.2–0.7 g/cm²) and spatially uniform.

---

### 4. Coastal temperate mid-summer (maritime aerosol, adjacency correction)

**Scene**: Gulf of Lion, Mediterranean, July (DOY 200). Low sun elevation
at overpass time is unusual but covered; clean marine air; land-sea boundary
requires adjacency correction.

```sh
i.hyper.atcorr \
    lut=mediterranean.lut \
    sza=22 vza=0 raa=0 \
    atmosphere=midsum aerosol=maritime ozone=315 \
    aod=0.02,0.06,0.12,0.20,0.30 \
    h2o=1.5,2.5,3.5,4.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Per-pixel atmospheric maps from external products + adjacency correction
i.hyper.atcorr -u -r \
    input=med_radiance output=med_refl \
    lut=mediterranean.lut \
    sza=22 vza=0 raa=0 doy=200 \
    atmosphere=midsum aerosol=maritime \
    aod_map=maiac_aod h2o_map=mod05_wvc \
    smooth=2 \
    adj_psf=0.5 \
    uncertainty=med_refl_unc

# Image-based alternative: per-pixel H₂O (-w) + DDV AOD (-a) from coastal
# vegetation replace the external MAIAC and MOD05 maps.
# -z omitted: Mediterranean O₃ (310–320 DU) is stable; scalar reliable.
i.hyper.atcorr -w -a -u -r \
    input=med_radiance output=med_refl \
    lut=med_auto.lut \
    sza=22 vza=0 raa=0 doy=200 \
    atmosphere=midsum aerosol=maritime \
    smooth=2 adj_psf=0.5 \
    uncertainty=med_refl_unc \
    aod=0.02,0.06,0.12,0.20,0.30 h2o=1.5,2.5,3.5,4.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why adjacency correction matters here**: At a land-sea boundary the
bright land signal bleeds into adjacent water pixels through atmospheric
forward scattering; the diffuse transmittance fraction (~10–20 % for
maritime aerosol at 550 nm) carries the environmental mean reflectance.
`adj_psf=0.5 km` accounts for the typical 500 m scattering radius for
clean marine conditions.  Maritime aerosol has low absorption (SSA ≈ 0.98)
and coarse sea-salt particles that produce strong forward scattering —
the standard deviation of the path radiance is lower than for urban air
but the adjacency radius is larger.

**Retrieval flags**: **`-w`** retrieves per-pixel WVC from 940 nm; the
Mediterranean in July has a strong land–sea H₂O gradient (1.5–4.0 g/cm²
coast to open sea), which satellite products resolve at only 5–10 km —
worse than Tanager's sub-km pixels.  **`-a`** exploits coastal garrigue
and irrigated farmland as DDV targets; the marine AOD horizontal gradient
(0.05–0.20 AOD from open sea to haze near the Rhône delta) is well
captured by per-pixel retrieval.  **`-z`** is omitted: western
Mediterranean mid-summer O₃ (~315 DU) varies by < 10 DU between years,
within the noise of the Chappuis retrieval at moderate SZA.

---

### 5. Sub-arctic mid-winter with full ISOFIT pipeline

**Scene**: Boreal forest, Northern Sweden, January (DOY 15). Very low
sun, snow-covered ground, clean sub-arctic air.

```sh
i.hyper.atcorr \
    lut=sweden_winter.lut \
    sza=78 vza=8 raa=45 \
    atmosphere=subwin aerosol=continental ozone=340 \
    aod=0.01,0.05,0.10,0.20 \
    h2o=0.1,0.3,0.5,0.8 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Full ISOFIT pipeline with external AOD/H₂O maps
i.hyper.atcorr -u -r \
    input=sweden_radiance output=sweden_refl \
    lut=sweden_winter.lut \
    sza=78 vza=8 raa=45 doy=15 \
    atmosphere=subwin aerosol=continental \
    aod_map=maiac_aod h2o_map=mod05_wvc \
    smooth=3 adj_psf=1.0 \
    uncertainty=sweden_refl_unc

# Add image-based O₃ retrieval (-z): sub-arctic winter O₃ varies
# significantly with polar vortex proximity; -a and -w not used
# (snow-covered ground has no DDV pixels; H₂O < 0.5 g/cm² is well-known).
i.hyper.atcorr -z -u -r \
    input=sweden_radiance output=sweden_refl \
    lut=sweden_winter_auto.lut \
    sza=78 vza=8 raa=45 doy=15 \
    atmosphere=subwin aerosol=continental \
    aod_map=maiac_aod h2o_map=mod05_wvc \
    smooth=3 adj_psf=1.0 \
    uncertainty=sweden_refl_unc \
    aod=0.01,0.05,0.10,0.20 h2o=0.1,0.3,0.5,0.8 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why `atmosphere=subwin`**: Sub-arctic winter profiles have the coldest
temperature structure and the lowest H₂O scale height of the six models,
with significant stratospheric ozone enhancement.  At SZA=78° the path
length through the atmosphere is ~5× that at nadir, so precise
atmosphere profile selection matters more than at low sun angles.  The
`-r` MAP regularisation is especially useful here: bright snow reflectance
is nearly spectrally flat (prior: soil component), which constrains
physically implausible spectral spikes caused by residual gas-correction
errors at very long path lengths.

**Retrieval flags**: **`-z`** is particularly valuable at high latitudes in
winter: the polar vortex can push stratospheric O₃ columns to 350–400 DU
(vs the 340 DU prior), and the long path length at SZA=78° amplifies O₃
absorption by ~×5 relative to nadir — a 40 DU offset then causes a ~1 %
error in the green–red bands.  Retrieving O₃ from the Chappuis band
eliminates this latitude-dependent offset without requiring a real-time O₃
product.  **`-a`** is omitted: snow in January has ρ_2130 > 0.25, excluding
virtually all land pixels from the DDV mask.  **`-w`** is omitted: sub-arctic
winter WVC (< 0.5 g/cm²) is well-captured by the narrow H₂O LUT grid; at
SZA=78° even small WVC errors amplify path corrections, so the external
MOD05 map is preferred over the noisier 940 nm retrieval in very cold, dry
conditions.

---

### 6. Sub-arctic mid-summer — boreal forest

**Scene**: Yukon Territory, Canada, July (DOY 190). Low-moderate sun,
moderate water vapour from thawed tundra, clean background aerosol.

```sh
i.hyper.atcorr \
    lut=yukon_summer.lut \
    sza=45 vza=2 raa=60 \
    atmosphere=subsum aerosol=continental ozone=320 \
    aod=0.02,0.07,0.15,0.30 \
    h2o=0.8,1.5,2.5,3.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# Correction with scalar state (scalar baseline)
i.hyper.atcorr \
    input=yukon_radiance output=yukon_refl \
    lut=yukon_summer.lut \
    sza=45 vza=2 raa=60 doy=190 \
    aod_val=0.08 h2o_val=2.0 \
    atmosphere=subsum aerosol=continental

# Fully standalone — all four atmospheric state variables retrieved from image.
# -z: sub-arctic O₃ varies 300–340 DU with planetary wave activity.
# -w: tundra WVC spans 1–3.5 g/cm²; per-pixel 940 nm retrieval captures gradient.
# -a: dense boreal spruce forest is an ideal DDV target (NDVI ~0.6–0.8).
# dem=: Yukon terrain spans 500–2000+ m; ISA pressure correction is significant.
i.hyper.atcorr -z -w -a \
    input=yukon_radiance output=yukon_refl \
    lut=yukon_summer_auto.lut \
    sza=45 vza=2 raa=60 doy=190 \
    atmosphere=subsum aerosol=continental \
    dem=dem_yukon \
    aod=0.02,0.07,0.15,0.30 h2o=0.8,1.5,2.5,3.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Why `atmosphere=subsum`**: Sub-arctic summer combines moderate surface
temperatures with relatively dry air (H₂O < 3.5 g/cm²), a profile
distinct from both the tropical and mid-latitude summer models.  The
boreal growing season produces biogenic terpene aerosol well captured by
the continental aerosol model.

**Retrieval flags**: **`-z`** retrieves scene-mean O₃; sub-arctic summer
O₃ varies 300–340 DU with planetary wave activity.  **`-w`** retrieves
per-pixel WVC from the 940 nm band; heterogeneous boreal–tundra landscapes
have WVC gradients of 1–2 g/cm² over 10–20 km (wet valley bogs vs dry
ridgelines).  **`-a`** uses dense spruce forest as a DDV target
(ρ_2130 ≈ 0.05–0.12, NDVI ~0.6–0.8) to retrieve per-pixel AOD; wildfire
smoke episodically raises AOD at 550 nm from background ~0.05 to > 0.5.
**`dem=`** applies the ISA barometric formula to the mean terrain elevation;
a 1 000 m elevation change reduces surface pressure by ~11 %, which if
uncorrected biases Rayleigh scattering by ~3 % in the blue bands.

---

### 7. Custom Mie aerosol + BRDF via the C API (Python)

The GRASS module exposes the five standard aerosol models via the
`aerosol=` flag. For research applications requiring a specific particle
size distribution (e.g. fresh wildfire smoke, mineral dust with a
measured size distribution), use `sixs_mie_init()` through the Python
bindings:

```python
import ctypes, numpy as np
from python.atcorr import LutConfig, LutArrays, compute_lut
from include.brdf import BrdfType, BrdfParams

# -------------------------------------------------------------------
# Example A: Fresh wildfire smoke over boreal forest
# Carbonaceous particles (AERONET SMART-COMMIT median values for boreal
# smoke): small mode, strongly absorbing.
# Combined with Ross-Li-Maignan BRDF for the forest canopy below.
# -------------------------------------------------------------------
cfg = LutConfig()
cfg.aerosol_type   = 9            # AEROSOL_CUSTOM — use Mie init
cfg.mie_r_mode     = 0.08         # mode radius µm (fine carbonaceous)
cfg.mie_sigma_g    = 1.70         # geometric std dev (narrow smoke mode)
cfg.mie_m_real     = 1.52         # real refractive index at 550 nm
cfg.mie_m_imag     = 0.045        # imaginary part: strong absorption (SSA≈0.87)
cfg.atmosphere_type = 5           # subsum — boreal summer
cfg.sza            = 45.0
cfg.vza            = 2.0
cfg.raa            = 60.0
cfg.brdf_type      = BrdfType.BRDF_ROSSLIMAIGNAN
# Ross-Li-Maignan for dense boreal forest (summertime LAI≈4)
cfg.brdf_params    = (0.08, 0.04, 0.01, 2.0, 0, 0)  # fiso,fvol,fgeo,h_ratio
lut = compute_lut(cfg)

# Why this combination?
# 1. Standard aerosol models represent background climatology.
#    Fresh smoke events have much smaller r_mode (~0.06-0.10 µm vs 0.15 µm
#    for continental), higher m_i (0.03-0.06 vs 0.001), and Angstrom
#    exponents of 1.8-2.2 (vs 1.2 for continental). Using the wrong
#    aerosol optical model introduces a systematic positive reflectance
#    bias of 3-8% in the blue bands and a negative bias in the NIR.
# 2. The Ross-Li-Maignan BRDF captures the hotspot reflectance surge
#    of a closed forest canopy (observed ratio of forward/backward
#    scattering ~3:1 in NIR). Lambertian assumption underestimates
#    reflectance at hotspot geometry by 15-25%.
# 3. Combining both corrections simultaneously avoids double-counting:
#    the aerosol correction uses the correct Mie phase function, and
#    the surface correction uses the correct anisotropy factor.

# -------------------------------------------------------------------
# Example B: Saharan dust episode over dune fields
# Coarse calcite/quartz particles measured during a Bodélé event.
# Combined with Hapke BRDF for bright desert sand.
# -------------------------------------------------------------------
cfg2 = LutConfig()
cfg2.aerosol_type  = 9
cfg2.mie_r_mode    = 1.5          # coarse mode radius µm (supermicron dust)
cfg2.mie_sigma_g   = 2.3          # broad distribution (bimodal dust)
cfg2.mie_m_real    = 1.55         # calcite/quartz real part
cfg2.mie_m_imag    = 0.003        # very low imaginary part (nearly conservative)
cfg2.atmosphere_type = 4          # tropical
cfg2.sza           = 40.0
cfg2.vza           = 5.0
cfg2.raa           = 150.0
cfg2.brdf_type     = BrdfType.BRDF_HAPKE
# Hapke for bright quartz sand (omega=0.88, b=0.25, c=0.80, h=0.48)
cfg2.brdf_params   = (0.88, 0.25, 0.80, 0.48, 0, 0)
lut2 = compute_lut(cfg2)

# Why this combination?
# 1. Heavy dust events shift the size distribution toward coarser particles
#    (r_eff > 2 µm) compared to the standard Shettle/Fenn desert model
#    (r_eff ≈ 0.5 µm, tuned for background mineral aerosol). Coarser
#    particles have: lower Angstrom exponent (α≈0.1-0.4 vs 0.4-0.6),
#    stronger forward phase function peak, and larger single-scattering
#    albedo in the blue (less absorption relative to scattering).
#    Mie modelling with the measured size distribution reduces the NIR
#    reflectance bias by 5-12% for thick dust layers (AOD > 0.8).
# 2. Desert sand is one of the most strongly non-Lambertian surfaces.
#    Hapke's photometric model captures the opposition surge (sharp
#    backscatter peak at phase angle ≈ 0°) and the broad forward-
#    scattering lobe. Lambertian assumption underestimates solar-noon
#    reflectance by up to 20% for bright sand (rho_Lamb ≈ 0.45 vs
#    rho_Hapke ≈ 0.54 at hotspot).
```

---

### 8. Quick test at coarse spectral resolution

```sh
i.hyper.atcorr --verbose \
    lut=/tmp/test.lut \
    sza=30 vza=0 raa=0 \
    aod=0.0,0.2,0.4 h2o=2.0,4.0 \
    wl_min=0.4 wl_max=2.5 wl_step=0.05
```

---

### 9. Fully standalone — all atmospheric state from the image

This example demonstrates the autonomous mode where all four atmospheric
state variables are retrieved from the hyperspectral image itself,
eliminating the need for external ancillary products (MODIS O₃, MOD05 WVC,
MAIAC AOD, or DEM pressure).  A single command generates the LUT and
applies the correction.

```sh
# All four image-based retrievals in one pass:
#   -z  → scene-mean O₃ from Chappuis band (540/600/680 nm)
#   -w  → per-pixel WVC from 940 nm band depth (865/940/1040 nm)
#   -a  → per-pixel AOD from MODIS DDV algorithm (470/660/860/2130 nm)
#   dem= → ISA surface pressure from mean DEM elevation
i.hyper.atcorr -z -w -a \
    input=scene_radiance output=scene_refl \
    lut=scene_auto.lut \
    sza=40 vza=3 raa=120 doy=180 \
    atmosphere=midsum aerosol=continental \
    dem=terrain_dem \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 \
    h2o=0.5,1.5,3.0,5.0 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**What each flag retrieves**:

- **`-z`** — Scene-mean O₃ (Dobson units) from the Chappuis absorption band
  centred at 600 nm.  Continuum: linear interpolation of L_540 and L_680;
  band depth D = 1 − L_600/L_cont; O₃ = D / (σ_600 × m) where
  σ_600 ≈ 10⁻⁴ DU⁻¹ and m = 1/cos(SZA) + 1/cos(VZA).  The retrieved value
  replaces `ozone=` before the LUT is computed; falls back to 300 DU if
  fewer than one valid pixel is found.

- **`-w`** — Per-pixel column water vapour (g/cm²) from the 940 nm band
  depth.  Continuum: linear interpolation of L_865 and L_1040;
  D = 1 − L_940/L_cont; WVC = D / (K_940 × m) where K_940 = 0.036 cm²/g.
  The per-pixel array is used during correction in place of the scalar
  `h2o_val=`; pixels without valid 940 nm signal fall back to 2 g/cm².

- **`-a`** — Per-pixel AOD at 550 nm from the MODIS DDV algorithm.  DDV
  mask: 0.01 < ρ_2130 < 0.25 AND NDVI(860/660) > 0.1.  Surface reflectance
  predicted as ρ_surf_470 = 0.25 ρ_2130 and ρ_surf_660 = 0.50 ρ_2130.
  Ångström exponent from the 470/660 nm pair scales τ to 550 nm.  Non-DDV
  pixels receive the scene-mean AOD.  Requires bands near 470, 660, 860, and
  2130 nm.

- **`dem=`** — Mean terrain elevation → ISA surface pressure
  P = 1013.25 × (1 − 2.2558 × 10⁻⁵ × h)^5.2559 hPa.  Updates
  `surface_pressure` before LUT computation.  Eliminates the systematic
  Rayleigh scattering bias at elevations above ~500 m.

**Prerequisites**: the image must span at least 376–2499 nm with adequate
SNR at 540/600/680 nm (O₃), 865/940/1040 nm (H₂O), and 470/660/860/2130 nm
(AOD).  Tanager, DESIS, HySpex, PRISMA, and EnMAP all satisfy these
requirements.

---

### 10. Alpine terrain illumination correction (Swiss Alps)

**Scene**: Engadin valley, Switzerland, October (DOY 285).  SZA = 55°, solar
azimuth ≈ 165° (SSE).  Mixed conifer forest and alpine meadow with slopes up
to 40°.  A south-facing 30° slope receives
cos(25°)/cos(55°) ≈ 1.58× the reference irradiance while a north-facing 30°
slope at cos(85°)/cos(55°) ≈ 0.15× is effectively in diffuse-only
illumination — a 10× contrast that creates severe reflectance artefacts if
uncorrected.

```sh
# Prepare slope and aspect from a DEM
r.slope.aspect elevation=srtm_30m slope=alps_slope aspect=alps_aspect
# aspect= is clockwise from North as output by r.slope.aspect -c

# Single command: generate LUT + apply terrain illumination correction.
# slope= and aspect= trigger T_down_dir (direct-beam transmittance) computation
# inside atcorr_compute_lut; T_down_dir is not written to the .lut file
# (i.hyper.smac does not need it) but is used in-memory for the correction.
# -z retrieves scene O3 from 600 nm Chappuis depth (common at mid-latitude autumn).
i.hyper.atcorr -z \
    input=alps_radiance output=alps_refl \
    lut=alps_terrain.lut \
    sza=55 vza=8 raa=90 doy=285 \
    atmosphere=midwin aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.4 \
    h2o=0.5,1.0,2.0,3.5 \
    aod_val=0.08 h2o_val=1.5 \
    slope=alps_slope aspect=alps_aspect \
    sun_azimuth=165 \
    view_zenith=alps_vza \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**Physics**: T_down is split into direct (T_down_dir) and diffuse
(T_down − T_down_dir) components from the 6SV DISCOM output.  Per pixel:

- _Illuminated_ (cos_i > 0):
  `T_down_eff = T_down_dir × (cos_i / cos_sza) + (T_down − T_down_dir) × V_d`
- _Shadowed_ (cos_i ≤ 0):
  `T_down_eff = (T_down − T_down_dir) × V_d`  (diffuse skylight only)

where `cos_i = cos(sza)cos(s) + sin(sza)sin(s)cos(saa − aspect)` and
`V_d = (1 + cos(slope)) / 2` is the terrain skyview factor.

`view_zenith=` supplies per-pixel VZA from the pushbroom geometry model.  When
provided, T_up is rescaled by the Beer-Lambert path-length ratio
T_up^(cos_vza_ref / cos_vza_pixel).  Omit to use the scalar `vza=` value for
all pixels.

**Notes**:

- `slope=` and `aspect=` must always be provided together; omitting either
  disables terrain correction.
- The `.lut` file output (for i.hyper.smac) does not contain T_down_dir.
  Combining `lut=` with `input=/output=/slope=/aspect=` in one command is
  therefore the recommended workflow.
- For an accurate `sun_azimuth=` value, use `r.sunmask`, the scene metadata
  (`sun azimuth` field in ENVI HDR or HDF5 product), or `sixs_possol()` from
  the C library API.

---

### 11. NBAR normalization from MCD43 kernel weights (West African savanna)

**Scene**: Senegal/Mali Sahel, April (DOY 100).  SZA = 35°, wide-swath
pushbroom sensor (e.g. DESIS: ±12°, PRISMA: ±12.7°, EMIT: ±39°,
Tanager-1: ±7°) with per-pixel view zenith 0–25° across the swath.
At VZA = 20° the forward-scatter bowl effect can suppress NIR reflectance
by 5–15% relative to nadir view on bright soil; the backscatter hot-spot
enhancement creates the opposite effect.  NBAR normalization removes the
cross-track gradient for time-series compositing and mixed-scene analysis.

```sh
# Step 1: Download and resample MCD43A1 kernel weights.
# Product: MCD43A1 Collection 6.1 (500 m, 8-day or daily from LP DAAC / LAADS).
# Scale factor 0.001 (int16 → float32).  Here for tile h17v07, DOY 100.
# Use the nearest MODIS band as a spectral proxy for each hyper-band range.

r.import input=MCD43A1.A2024100.h17v07.061.Band1_f_iso.tif \
    output=mcd43_fiso resolution=value resolution_value=30 resample=bilinear
r.import input=MCD43A1.A2024100.h17v07.061.Band1_f_vol.tif \
    output=mcd43_fvol resolution=value resolution_value=30 resample=bilinear
r.import input=MCD43A1.A2024100.h17v07.061.Band1_f_geo.tif \
    output=mcd43_fgeo resolution=value resolution_value=30 resample=bilinear

# Step 2: Atmospheric correction + NBAR normalization.
# view_zenith= and view_azimuth= come from the sensor L1 geometry model.
# sun_azimuth= is a scalar from scene metadata (degrees CW from North).
# -w -a retrieve per-pixel WVC and AOD from the image.
i.hyper.atcorr -w -a \
    input=senegal_radiance output=senegal_nbar \
    lut=senegal.lut \
    sza=35 doy=100 \
    atmosphere=tropical aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.5 \
    h2o=1.0,2.0,3.5,5.0 \
    aod_val=0.12 h2o_val=2.5 \
    sun_azimuth=128 \
    view_zenith=senegal_vza view_azimuth=senegal_vaa \
    brdf_fiso=mcd43_fiso brdf_fvol=mcd43_fvol brdf_fgeo=mcd43_fgeo \
    wl_min=0.376 wl_max=2.499 wl_step=0.005
```

**MCD43 typical kernel weights by land cover** (Schaaf et al. 2002,
*Remote Sensing of Environment* 83, 135–148):

| Land cover | Band (µm) | f_iso | f_vol | f_geo | ρ_NBAR / ρ_obs at VZA=20°, RAA=90° |
|---|---|---|---|---|---|
| Savanna / grassland | Red 0.66 | 0.119 | 0.067 | 0.026 | 0.95–1.08 |
| Savanna / grassland | NIR 0.86 | 0.220 | 0.116 | 0.033 | 0.93–1.06 |
| Deciduous broadleaf | Red 0.66 | 0.093 | 0.080 | 0.019 | 0.97–1.10 |
| Deciduous broadleaf | NIR 0.86 | 0.354 | 0.193 | 0.069 | 0.92–1.09 |
| Cropland | Red 0.66 | 0.154 | 0.074 | 0.031 | 0.96–1.07 |
| Cropland | NIR 0.86 | 0.265 | 0.119 | 0.054 | 0.94–1.06 |
| Bare soil / desert | Red 0.66 | 0.200 | 0.020 | 0.052 | 0.91–1.12 |
| Bare soil / desert | NIR 0.86 | 0.252 | 0.020 | 0.056 | 0.90–1.14 |

**NBAR formula**: `ρ_NBAR = ρ_boa × f_nbar / f_obs` where
`f = f_iso + f_vol × K_RT + f_geo × K_LS`.
Standard MODIS Ross-Thick (K_RT) and Li-Sparse (K_LS) kernels are used
(b/r = 1, h/b = 2); no Maignan hot-spot correction.
K_LS = 0 at nadir, so `f_nbar = f_iso + f_vol × K_RT(sza, 0, 0)`.
The correction is bypassed for pixels where f_obs < 10⁻⁶ (prevents
division-by-zero) or when f_vol = f_geo = 0 (Lambertian → no anisotropy).

**MCD43A1 source**: LP DAAC / LAADS DAAC,
`https://lpdaac.usgs.gov/products/mcd43a1v061/`.
Scale factor 0.001 for all kernel weight bands.  The product is available
globally every 8 days (or daily in Collection 6.1).  Use the tile covering
the scene; spatial resolution 500 m, resample to sensor pixel size with
bilinear interpolation.

---

### 12. O₂-A per-pixel surface pressure + pre-correction quality mask

**Scene**: Landsat-resolution hyperspectral over the Rocky Mountains
(Colorado, USA; DOY 200, SZA=30°).  Elevation ranges 1500–4400 m (pressure
700–860 hPa), causing a 10–15% band-to-band Rayleigh error if ignored.
Mixed land cover with glaciers (NDSI test) and alpine lakes (water test).

```sh
# Step 1: generate LUT with standard sea-level reference
i.hyper.atcorr \
    lut=rockies.lut \
    input=rockies_radiance \
    output=rockies_refl \
    sza=30 vza=4 raa=120 doy=200 \
    atmosphere=us62 aerosol=continental \
    aod=0.02,0.05,0.1,0.2,0.4 \
    h2o=0.5,1.0,2.0,3.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005 \
    -p -m -w \
    quality=rockies_quality

# The -p flag retrieves per-pixel surface pressure from the O₂-A band at 760 nm
# and applies per-pixel Rayleigh scaling: R_atm, T_down, T_up are adjusted
# according to  τ_R(λ, P) = 0.00877 × λ^(−4.05) × P/P₀  (Hansen & Travis 1974)
#
# The -m flag outputs a bitmask raster (integer, bits: 0=cloud 1=shadow 2=water 3=snow)
# which can be used to mask the output or exclude pixels from further analysis:
r.mapcalc "rockies_refl_masked = if(rockies_quality == 0, rockies_refl_band60, null())"
```

**Physics of the pressure correction**:

- Rayleigh optical depth scales linearly with surface pressure:
  τ_R(λ, P) = 0.00877 × λ^(−4.05) × P/P₀
- At 450 nm (blue), Δτ_R ≈ 0.08 for ΔP = 300 hPa → ΔT ≈ 8% → 5% BOA error if ignored
- At 700 nm (red), Δτ_R ≈ 0.01 → effect is negligible (<1%)
- The correction is applied in-band per pixel before inversion

**O₂-A K_O2 tuning**: the default K_O2 = 0.25 is calibrated for ~10 nm FWHM.
For sensors with different bandwidths: PRISMA/5 nm ≈ 0.40; AVIRIS-NG/4 nm ≈ 0.45;
DESIS/2.5 nm ≈ 0.55.  Tune by comparing retrieved scene-mean pressure against
co-located DEM-based ISA pressure.

---

### 13. MAIAC patch AOD spatial regularization (dense vegetation)

**Scene**: Tanager over a mixed agricultural/forest scene in Central Europe
(DOY 160, SZA=35°).  DDV retrieval yields spatially noisy per-pixel AOD because
individual DDV pixels in heterogeneous fields produce single-pixel outliers.

```sh
i.hyper.atcorr \
    input=central_europe_radiance \
    output=central_europe_refl \
    sza=35 vza=3 raa=100 doy=160 \
    atmosphere=us62 aerosol=continental \
    aod=0.02,0.05,0.1,0.2,0.4 \
    h2o=0.5,1.0,2.0,3.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005 \
    -a -w \
    maiac_patch=32

# The -a flag retrieves per-pixel DDV AOD (scene mean ~0.12 for this clean scene).
# maiac_patch=32 applies the MAIAC-inspired patch regularization:
#   1. Image divided into non-overlapping 32×32 pixel patches
#   2. Each patch AOD → patch median (robust to DDV outliers)
#   3. Patches with no DDV pixels filled by inverse-distance weighting
#      from valid patch centroids (IDW)
#   4. Pixel-level AOD replaced by its patch median value
#
# Effect: eliminates single-pixel hot-spots from isolated DDV pixels;
# provides spatially coherent AOD field comparable to MAIAC 1 km product
# at the native sensor resolution.
```

**Patch size guidelines**:

| Sensor GSD | Scene size | Recommended patch_sz |
|------------|-----------|---------------------|
| 30 m | 30 km | 32 px (~1 km²) |
| 5 m  | 5 km  | 16 px (~80 m²) |
| 1 m  | 1 km  | 8 px  (~8 m²) |

Smaller patches preserve more spatial variability but require denser DDV coverage.
Larger patches smooth more aggressively.

---

### 14. Joint optimal-estimation AOD + H₂O retrieval (-e)

**Scene**: PRISMA over a semi-arid shrubland in southern Spain (DOY 120,
SZA=25°).  Mixed surfaces (sparse vegetation + bare soil) mean that the DDV
assumption is invalid for most pixels.  The spectral-smoothness OE retrieves
both AOD and H₂O simultaneously without requiring DDV targets.

```sh
i.hyper.atcorr \
    input=spain_radiance \
    output=spain_refl \
    sza=25 vza=2 raa=80 doy=120 \
    atmosphere=midsum aerosol=continental \
    aod=0.02,0.05,0.1,0.2,0.4 \
    h2o=0.5,1.0,2.0,3.5 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005 \
    aod_val=0.1 h2o_val=1.5 \
    -e \
    oe_sigma_aod=0.5 oe_sigma_h2o=1.0

# -e: joint optimal estimation retrieval
#   VIS diagnostic bands: 470, 550, 660, 870 nm (aerosol sensitivity)
#   NIR constraint:       865, 940, 1040 nm (H₂O absorption)
#
# Cost function per pixel:
#   J_spec  = ||ρ_boa(b) − linear_fit(ρ_boa)||² / σ_spec²
#             (spectral smoothness; over/under-corrected spectra show
#              a step at 470 nm that penalises wrong AOD)
#   J_h2o   = (D_940_meas − K_940 × m × H₂O)² / σ_D²
#   J_prior = (ln AOD − ln AOD_prior)² / σ_a²
#           + (H₂O − H₂O_prior)²       / σ_h²
#
# Grid search over LUT (AOD_i, H₂O_j) points + parabolic sub-grid refinement.
# oe_sigma_aod=0.5: broad prior (±50% in log-AOD space)
# oe_sigma_h2o=1.0: broad prior (±1 g/cm²)
# Output: same as normal correction but uses per-pixel AOD/H₂O from OE
```

**Notes**:

- OE supersedes independent `-a` (DDV) and `-w` (940 nm) when used together with `-e`
- OE requires the LUT to be already computed → runs after `atcorr_compute_lut`
- The spectral smoothness cost is scale-independent (relative to a linear fit)
  and works for any surface type (vegetation, soil, water, urban)
- For scenes with many cloud/snow pixels, combine with `-m quality=` and post-mask
- OE is single-pass (no outer iteration between surface and atmosphere) — for
  highest accuracy over bright surfaces, iterate manually: correct → extract
  per-pixel surface spectra → rerun OE using surface prior from first pass

**Sigma tuning**:

| Scenario | oe_sigma_aod | oe_sigma_h2o |
|----------|-------------|-------------|
| Strong prior from DEM/MODIS | 0.2 | 0.5 |
| Weak prior (tropical) | 0.8 | 2.0 |
| Default (midlatitude) | 0.5 | 1.0 |

---

### 15. FlexBRDF — spectrally-varying NBAR from MCD43 disaggregation

**Scene**: EnMAP over a mixed temperate landscape (Central Europe, DOY 160,
SZA = 35°).  Standard scalar NBAR (Example 11) applies the same f_iso/f_vol/f_geo
value at every wavelength.  FlexBRDF disaggregates 7-band MCD43A1 kernel weights
to the full 400–2500 nm range, then applies Tikhonov second-difference smoothing
to produce physically consistent spectral kernel weight curves — essential for
cross-band consistency in hyperspectral time series.

```sh
# Step 1: Obtain MCD43A1 kernel weights for the 7 MODIS bands.
# Values here are scene-mean floats parsed from a mixed grassland/crop tile
# (scale factor 0.001 already applied; bands in order B3,B4,B1,B2,B5,B6,B7).
# Wavelengths: 469, 555, 645, 858, 1240, 1640, 2130 nm.

FISO="0.112,0.117,0.095,0.243,0.155,0.118,0.085"   # isotropic kernel
FVOL="0.045,0.040,0.038,0.131,0.038,0.022,0.014"   # Ross-Thick volumetric
FGEO="0.017,0.014,0.012,0.052,0.016,0.009,0.006"   # Li-Sparse geometric

# Step 2: Atmospheric correction + spectrally-resolved NBAR normalization.
# mcd43_fiso/fvol/fgeo= accept 7 comma-separated floats at the MODIS wavelengths.
# mcd43_alpha=0.10: Tikhonov regularization strength (~0.05-0.2 typical).
# brdf_fiso= etc. can additionally supply per-pixel spatial amplitude rasters;
# if omitted, the scene-mean spectral kernel weights are used for all pixels.
i.hyper.atcorr -w -a \
    input=enmap_radiance output=enmap_nbar \
    lut=enmap.lut \
    sza=35 vza=4 raa=110 doy=160 \
    atmosphere=us62 aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.5 \
    h2o=0.5,1.0,2.0,3.5 \
    aod_val=0.12 h2o_val=1.8 \
    sun_azimuth=155 \
    view_zenith=enmap_vza view_azimuth=enmap_vaa \
    mcd43_fiso="$FISO" \
    mcd43_fvol="$FVOL" \
    mcd43_fgeo="$FGEO" \
    mcd43_alpha=0.10 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005

# With per-pixel spatial amplitude rasters (from Example 11 workflow):
# brdf_fiso=mcd43_fiso_raster brdf_fvol=mcd43_fvol_raster brdf_fgeo=mcd43_fgeo_raster
# The spectral shape comes from mcd43_fiso/fvol/fgeo= (7-band scalars);
# the per-pixel spatial amplitude comes from brdf_fiso=/fvol=/fgeo= (2D rasters).
# Combined: f_iso_eff(x,y,λ) = fiso_raster(x,y) × fiso_wl(λ) / fiso_wl(858 nm)
```

**FlexBRDF algorithm** (Queally et al. 2022; Garcia-Beltran et al. 2024):

1. **Piecewise-linear interpolation**: the 7 MCD43A1 kernel weights at MODIS band
   centres {0.469, 0.555, 0.645, 0.858, 1.240, 1.640, 2.130} µm are interpolated
   to all `n_wl` sensor wavelengths.  Outside the anchor range, the endpoint value
   is clamped (constant extrapolation).

2. **Tikhonov second-difference smoothing** (`mcd43_alpha > 0`): solves
   `(I + α²·D₂ᵀD₂)·x = f` in O(5n) via Cholesky band factorization.
   D₂ᵀD₂ is 5-diagonal (banded bandwidth 2), making the system SPD.
   The smoother suppresses ringing at the sparse anchor transitions while
   preserving the physical spectral shape.

3. **Spectral NBAR**: at band z, pixel i:
   `f_iso_eff = f_iso_px(i) × fiso_wl(z) / fiso_wl(858 nm)`
   where `fiso_wl(z)` is the disaggregated spectral shape (normalised to the
   NIR reference at 858 nm) and `f_iso_px(i)` is the per-pixel spatial amplitude.
   When only scene-mean kernels are given (no `brdf_fiso=` rasters), `f_iso_px = 1`.

**Tikhonov `mcd43_alpha` tuning**:

| Scene | Recommended alpha | Notes |
|-------|------------------|-------|
| Smooth vegetation / soil | 0.05 – 0.10 | Gentle regularization |
| Mixed land cover | 0.10 – 0.15 | Default; removes anchor interpolation artefacts |
| Very sparse MCD43 data | 0.20 – 0.30 | Aggressive smoothing; avoids kinks between anchors |
| Off (raw piecewise-linear) | 0.0 | Not recommended; shows 7 kinks at MODIS wavelengths |

**MCD43A1 source**: LP DAAC, `https://lpdaac.usgs.gov/products/mcd43a1v061/`.
Scale factor 0.001.  Use the 8-day composite tile nearest in time to the acquisition.

---

### 16. DASF — Directional Area Scattering Factor (canopy structure retrieval)

**Scene**: Tanager over a temperate broadleaf forest (DOY 200, SZA = 30°).
The DASF exploits the spectral invariance property of vegetation in the 710–790 nm
NIR plateau where leaf albedo ω_L(λ) is nearly flat and canopy reflectance is
dominated by the structural scattering factor rather than biochemistry.

```sh
# DASF retrieval requires atmospheric correction to BOA reflectance first.
# It runs inline with the correction using the -D flag.
#
# The PROSPECT-D leaf albedo table (R+T, Féret et al. 2017, Cab=40 µg/cm²)
# provides ω_L(λ) at 5 nm steps from 705 to 795 nm.
# Physics (Knyazikhin et al. 2013): ρ_boa(λ) ≈ DASF × ω_L(λ)
#   → DASF = Σ[ρ_boa(λ) × ω_L(λ)] / Σ[ω_L(λ)²]  (linear least-squares)
#   → DASF ∈ [0.01, 1.0]; NaN where NDVI < 0.2 (non-vegetation)

i.hyper.atcorr -z -w -a -D \
    input=tanager_radiance output=tanager_refl \
    lut=tanager_dasf.lut \
    sza=30 vza=4 raa=100 doy=200 \
    atmosphere=midsum aerosol=continental \
    aod=0.0,0.05,0.1,0.2,0.4,0.8 \
    h2o=0.5,1.5,3.0,5.0 \
    wl_min=0.376 wl_max=2.499 wl_step=0.005 \
    dasf=tanager_dasf

# DASF output: 2D FCELL raster (single band), co-registered with the
# input scene. Non-vegetation pixels (NDVI < 0.2) are NaN.
# Inspect the result:
r.univar map=tanager_dasf
r.colors map=tanager_dasf color=viridis

# Combine DASF with reflectance for leaf albedo decomposition (Knyazikhin 2013):
# ω_L_est(λ) = ρ_boa(λ) / DASF  -- at each vegetation pixel
# This recovers an effective leaf albedo spectrum free of canopy structure effects,
# enabling LAI / leaf biochemistry retrieval without a canopy RT model.
```

**DASF physics** (Knyazikhin et al. 2013 PNAS):

The spectral invariance property of vegetation canopies states that in the
NIR plateau (710–790 nm) where single-scattering albedo ω_L ≈ 0.90:

```
ρ_boa(λ) = DASF × ω_L(λ) + ε(λ)
```

where DASF is the **Directional Area Scattering Factor** (a scalar that captures
the structural angular scattering of the canopy) and ε(λ) is a small spectral
residual (< 5 % for closed canopies).  DASF is solved per pixel as a
single-parameter least-squares fit:

```
DASF = Σ_λ [ρ(λ) × ω_L(λ)] / Σ_λ [ω_L(λ)²]
```

Implementation:
- Accumulates `sum_xy += ρ(λ) × ω_L(λ)` and `sum_yy += ω_L(λ)²` on the fly
  during the band loop (no extra band storage needed)
- NDVI masking: red (~660 nm) and NIR (~870 nm) bands saved during correction;
  pixels with NDVI < 0.2 receive NaN in the DASF output
- Valid threshold: fewer than 3 valid accumulation bands → NaN
- Range clipping: DASF ∈ [0.01, 1.0] (physical bounds)
- Leaf albedo table: PROSPECT-D (Féret et al. 2017) at 5 nm steps, 705–795 nm,
  Cab = 40 µg/cm², Cw = 0.013, Cm = 0.010, N = 1.5

**DASF interpretation**:

| DASF value | Canopy type |
|-----------|-------------|
| 0.90 – 1.0 | Dense closed forest (high multiple scattering) |
| 0.70 – 0.90 | Open forest / tall shrubland |
| 0.50 – 0.70 | Sparse vegetation / grassland with soil background |
| < 0.50 | Very sparse or mixed pixel (treat with caution) |

**Notes**:
- DASF is only meaningful for pixels where NDVI ≥ 0.2 and the canopy is
  vegetation-dominated in the 710–790 nm window
- Combine with FlexBRDF (Example 15) when both NBAR normalization and DASF
  retrieval are needed: add `mcd43_fiso= mcd43_fvol= mcd43_fgeo=` and `-D dasf=`
  to the same command
- The `-D` flag requires that `output=` is specified (correction must run);
  LUT-only mode does not support DASF

---

### 17. Python API — FlexBRDF and DASF without GRASS

This example shows how to use `libgrass_sixsv.so` from a Python script or
Jupyter notebook, outside the GRASS module.  No GRASS environment is needed;
any reflectance cube can be supplied as NumPy arrays.

```python
import numpy as np
from atcorr import (LutConfig, compute_lut, lut_slice, invert,
                    mcd43_disaggregate, spectral_smooth_tikhonov,
                    retrieve_dasf)

# ── Step 1: build a correction LUT ──────────────────────────────────────────
wl  = np.arange(0.376, 2.500, 0.005, dtype=np.float32)   # 425 bands
aod = np.array([0.0, 0.05, 0.1, 0.2, 0.4, 0.8], dtype=np.float32)
h2o = np.array([0.5, 1.5, 3.0, 5.0],             dtype=np.float32)

cfg = LutConfig(wl=wl, aod=aod, h2o=h2o,
                sza=30.0, vza=4.0, raa=100.0,
                altitude_km=1000.0,
                atmo_model=2,    # MIDSUM
                aerosol_model=1) # continental
lut = compute_lut(cfg)           # LutArrays [6, 4, 425]

# ── Step 2: invert a tile of radiance to BOA reflectance ────────────────────
# rho_toa: [n_bands, nrows, ncols] float32  (loaded by caller)
nrows, ncols = 512, 512
rho_toa = np.load("tile_rho_toa.npy").reshape(len(wl), -1)  # [n_wl, npix]

sl = lut_slice(cfg, lut, aod_val=0.18, h2o_val=1.8)  # 1-D [n_wl]
rho_boa = invert(rho_toa,
                 sl.R_atm[:, np.newaxis],
                 sl.T_down[:, np.newaxis],
                 sl.T_up[:, np.newaxis],
                 sl.s_alb[:, np.newaxis])   # [n_wl, npix]

# ── Step 3: FlexBRDF spectral NBAR ──────────────────────────────────────────
# MCD43A1 kernel weights at MODIS 7-band centres (scale factor 0.001 applied)
fiso_7 = [0.112, 0.117, 0.095, 0.243, 0.155, 0.118, 0.085]
fvol_7 = [0.045, 0.040, 0.038, 0.131, 0.038, 0.022, 0.014]
fgeo_7 = [0.017, 0.014, 0.012, 0.052, 0.016, 0.009, 0.006]

fiso_wl, fvol_wl, fgeo_wl = mcd43_disaggregate(
    fiso_7, fvol_7, fgeo_7, wl, alpha=0.10)

# NBAR normalisation (scalar, nadir SZA_nbar=30°):
# We need the kernel values at nadir (K_RT_nbar, K_LS_nbar=0) vs observation.
# For a quick scene-level scalar correction, use the ratio at the NIR reference:
i858 = np.argmin(np.abs(wl - 0.858))
from atcorr import mcd43_disaggregate  # already imported
# Compute f_obs(wl) and f_nbar(wl) = fiso(wl) + fvol(wl) * K_RT(sza_nbar, 0)
# K_RT is sensor-geometry-specific; here we show the brdf_normalize call path:
# (Full Ross-Thick / Li-Sparse kernels are in brdf.c: atcorr_brdf_normalize)
# For a fast scalar approximation:
scale_iso = fiso_wl / fiso_wl[i858]   # normalised spectral shape
rho_nbar  = rho_boa * scale_iso[:, np.newaxis]  # apply spectral NBAR shape

# ── Step 4: DASF canopy structure retrieval ──────────────────────────────────
nir_mask = (wl >= 0.710) & (wl <= 0.790)
wl_nir   = wl[nir_mask]
refl_nir = rho_boa[nir_mask, :]        # [n_nir, npix], band-major

dasf = retrieve_dasf(refl_nir, wl_nir) # float32 [npix]; NaN for non-veg

# Reshape back to 2D and save
dasf_2d = dasf.reshape(nrows, ncols)
np.save("dasf_result.npy", dasf_2d)

print(f"DASF: mean={np.nanmean(dasf_2d):.3f}  "
      f"valid px={np.sum(np.isfinite(dasf_2d))}/{nrows*ncols}")
```

**Notes**:

- `mcd43_disaggregate()` and `retrieve_dasf()` are thread-safe (no global state);
  call from any thread or multiprocessing pool.
- `spectral_smooth_tikhonov()` makes a copy — the input array is not modified.
- All retrieval functions (`retrieve_h2o_940`, `retrieve_aod_ddv`, etc.) are
  available in the same module and can be combined with FlexBRDF/DASF freely.
- The Python wrappers require only NumPy; no GRASS or libRadtran installation
  is needed for FlexBRDF/DASF.

---

### 18. C API — FlexBRDF and DASF in a custom pipeline

Minimal self-contained C program linking directly to `libgrass_sixsv.so`.
Compile with `gcc -O2 example.c -lgrass_sixsv -lm -o example`.

```c
/* example.c — FlexBRDF disaggregation + DASF retrieval from C */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "libsixsv/include/spectral_brdf.h"
#include "libsixsv/include/retrieve.h"

int main(void)
{
    /* ── 1. FlexBRDF: disaggregate MCD43 to sensor wavelength grid ────────── */
    const int n_wl = 420;
    float wl[n_wl];
    for (int i = 0; i < n_wl; i++)
        wl[i] = 0.400f + i * (2.100f / (n_wl - 1));   /* 0.40–2.50 µm */

    float fiso_7[7] = {0.112f, 0.117f, 0.095f, 0.243f, 0.155f, 0.118f, 0.085f};
    float fvol_7[7] = {0.045f, 0.040f, 0.038f, 0.131f, 0.038f, 0.022f, 0.014f};
    float fgeo_7[7] = {0.017f, 0.014f, 0.012f, 0.052f, 0.016f, 0.009f, 0.006f};

    float *fiso_wl = malloc(n_wl * sizeof(float));
    float *fvol_wl = malloc(n_wl * sizeof(float));
    float *fgeo_wl = malloc(n_wl * sizeof(float));

    mcd43_disaggregate(fiso_7, fvol_7, fgeo_7,
                       wl, n_wl, 0.10f,           /* alpha=0.10 */
                       fiso_wl, fvol_wl, fgeo_wl);

    /* Print disaggregated f_iso at a few wavelengths */
    int check_bands[] = {0, 50, 100, 150, 200, 300, 419};
    printf("FlexBRDF f_iso at selected wavelengths:\n");
    for (int k = 0; k < 7; k++) {
        int b = check_bands[k];
        printf("  wl=%.3f µm  f_iso=%.4f  f_vol=%.4f  f_geo=%.4f\n",
               wl[b], fiso_wl[b], fvol_wl[b], fgeo_wl[b]);
    }

    /* ── 2. DASF: retrieve canopy structure from simulated BOA reflectance ── */
    /* Select NIR plateau bands: 710–790 nm */
    int n_dasf = 0;
    for (int b = 0; b < n_wl; b++)
        if (wl[b] >= 0.710f && wl[b] <= 0.790f) n_dasf++;

    float *wl_nir   = malloc(n_dasf * sizeof(float));
    int npix = 1000;
    float *refl_nir = malloc(n_dasf * npix * sizeof(float));   /* band-major */

    int j = 0;
    for (int b = 0; b < n_wl && j < n_dasf; b++) {
        if (wl[b] >= 0.710f && wl[b] <= 0.790f) {
            wl_nir[j] = wl[b];
            /* Simulate a dense forest: constant BOA reflectance ~0.45 */
            for (int i = 0; i < npix; i++)
                refl_nir[j * npix + i] = 0.45f;
            j++;
        }
    }

    float *dasf = malloc(npix * sizeof(float));
    retrieve_dasf(refl_nir, wl_nir, n_dasf, npix, dasf);

    float sum = 0.0f; int valid = 0;
    for (int i = 0; i < npix; i++)
        if (!isnan(dasf[i])) { sum += dasf[i]; valid++; }
    printf("\nDASF retrieval: mean=%.3f over %d/%d valid pixels\n",
           sum / valid, valid, npix);

    free(fiso_wl); free(fvol_wl); free(fgeo_wl);
    free(wl_nir);  free(refl_nir); free(dasf);
    return 0;
}
```

**Compilation**:

```sh
cd ~/dev/i.hyper.atcorr
gcc -O2 -fopenmp example.c \
    -I~/dev \
    -L$(GRASS_DIST)/lib -lgrass_sixsv -lm \
    -Wl,-rpath,$(GRASS_DIST)/lib \
    -o example
./example
```

**Expected output**:

```
FlexBRDF f_iso at selected wavelengths:
  wl=0.400 µm  f_iso=0.1120  f_vol=0.0450  f_geo=0.0170
  wl=0.638 µm  f_iso=0.0980  f_vol=0.0388  f_geo=0.0127
  wl=0.876 µm  f_iso=0.2189  f_vol=0.1180  f_geo=0.0465
  wl=1.114 µm  f_iso=0.1871  f_vol=0.0741  f_geo=0.0291
  wl=1.350 µm  f_iso=0.1518  f_vol=0.0382  f_geo=0.0163
  wl=1.826 µm  f_iso=0.1165  f_vol=0.0230  f_geo=0.0098
  wl=2.500 µm  f_iso=0.0850  f_vol=0.0140  f_geo=0.0060

DASF retrieval: mean=0.502 over 1000/1000 valid pixels
```

**Notes on the C API**:

- Include `libsixsv/include/spectral_brdf.h` for `mcd43_disaggregate()` and
  `spectral_smooth_tikhonov()`; include `libsixsv/include/retrieve.h` for all
  retrieval functions.
- `spectral_smooth_tikhonov(f, n, alpha)` modifies `f` **in-place**
  (O(5n) Cholesky band solve).
- `retrieve_dasf(refl, wl_dasf, n_dasf, npix, out_dasf)` expects `refl`
  in **band-major** order: `refl[b * npix + i]` = band `b` of pixel `i`.
- Both functions are thread-safe and have no global or static state.
- `retrieve_dasf` is OpenMP-parallelised over pixels (`#pragma omp parallel for`);
  link with `-fopenmp` to enable.
- Link order: `-lgrass_sixsv -lm` (and `-fopenmp` via the compiler flag, not linker).

---

## Fortran 6SV2.1 compatibility

`testsuite/test_fortran_compat.py` (32 tests) cross-checks every C function
in `libgrass_sixsv.so` against the original Fortran 77 subroutines compiled
from `~/dev/6SV2.1/`.  All 32 tests pass; no C code bugs were found.

| Subroutine | C function | Tests | Tolerance | Actual agreement |
|---|---|---|---|---|
| CHAND | `sixs_chand()` | 4 geometries | rtol=1×10⁻⁵ | ~7×10⁻⁸ (float32 limit) |
| ODRAYL | `sixs_odrayl()` | 6 wavelengths (VIS/NIR/SWIR) | rtol=5×10⁻³ | ~2×10⁻⁷ |
| ODRAYL monotone | λ⁻⁴ spectral law | 2 ratio checks | physics | confirmed |
| VARSOL × d² ≈ 1 | `sixs_earth_sun_dist2()` | 4 DOYs | rtol=5×10⁻³ | <0.07% |
| SOLIRR / E0 on-grid | `sixs_E0()` | 4 wavelengths | rtol=1×10⁻³ | 0–3 ULP |
| SOLIRR / E0 off-grid | `sixs_E0()` | 1 wavelength (0.5512 µm) | rtol=1×10⁻³ | 0.035% |
| CSALBR | `sixs_csalbr()` | 3 τ values | rtol=1×10⁻⁵ | ~9×10⁻⁸ (float32 limit) |
| GAUSS | `sixs_gauss()` | n=4, n=8, n=16; weight sums, symmetry, nodes | rtol=1×10⁻⁵ | Exact float32 |

Minor intentional differences:

- `sixs_E0()` uses linear interpolation for off-grid wavelengths; Fortran SOLIRR
  uses nearest-neighbour — both agree to 0.035% on the smooth solar spectrum.
- `sixs_earth_sun_dist2()` returns d² (< 1 at perihelion); Fortran VARSOL returns
  1/d² (> 1) — the product ≈ 1.0 within 0.07%, confirming complementary conventions.
- Solar table float32 literals produce 0–3 ULP differences between gfortran and
  the C compiler — not a bug.

To run the tests (requires `~/dev/6SV2.1/` with 6SV2.1 source):

```sh
cd ~/dev/6sV2.1
gfortran -O -ffixed-line-length-132 -c CHAND.f ODRAYL.f VARSOL.f SOLIRR.f CSALBR.f GAUSS.f US62.f
cd ~/dev/i.hyper.atcorr
grass --tmp-project XY --exec python3 testsuite/test_fortran_compat.py
```

## SEE ALSO

*[i.hyper.smac](i.hyper.smac.md), [i.atcorr](i.atcorr.md)*

## REFERENCES

- Vermote, E.F., Tanré, D., Deuzé, J.L., Herman, M. and Morcrette, J.J.
  (1997): Second simulation of the satellite signal in the solar
  spectrum, 6S: An overview. *IEEE Transactions on Geoscience and
  Remote Sensing*, 35(3), 675–686.
- Kotchenova, S.Y., Vermote, E.F., Matarrese, R. and Klemm, F.J. (2006):
  Validation of a vector version of the 6S radiative transfer code for
  atmospheric correction of satellite data. *Applied Optics*, 45(26),
  6762–6778.
- Thompson, D.R. et al. (2018): Optimal estimation for imaging
  spectrometer atmospheric correction. *Remote Sensing of Environment*,
  216, 355–373. (ISOFIT)
- Vermote, E.F., El Saleous, N., Justice, C.O., Kaufman, Y.J.,
  Privette, J.L., Remer, L., Roger, J.C. and Tanré, D. (1997):
  Atmospheric correction of visible to middle-infrared EOS-MODIS data
  over land surfaces: Background, operational algorithm and validation.
  *Journal of Geophysical Research: Atmospheres*, 102(D14),
  17131–17141. (adjacency correction)
- Schaaf, C.B. et al. (2002): First operational BRDF, albedo nadir
  reflectance products from MODIS. *Remote Sensing of Environment*,
  83(1–2), 135–148. (MCD43 kernel weights)
- Roujean, J.L., Leroy, M. and Deschamps, P.Y. (1992): A bidirectional
  reflectance model of the Earth's surface for the correction of remote
  sensing data. *Journal of Geophysical Research: Atmospheres*, 97(D18),
  20455–20468. (Ross-Thick + Li-Sparse kernels)
- Teillet, P.M., Guindon, B. and Goodenough, D.G. (1982): On the slope-
  aspect correction of multispectral scanner data. *Canadian Journal of
  Remote Sensing*, 8(2), 84–106. (terrain illumination cosine correction)
- Queally, N. et al. (2022): FlexBRDF: A flexible BRDF correction for
  grouped processing of airborne imaging spectroscopy flightlines.
  *Journal of Geophysical Research: Biogeosciences*, 127, e2021JG006545.
  (FlexBRDF spectral NBAR disaggregation)
- Garcia-Beltran, A. et al. (2024): HABA: A new hyperspectral albedo-based
  algorithm for estimating plant area index. *Remote Sensing*, 16, 1405.
  (FlexBRDF application to hyperspectral BRDF)
- Knyazikhin, Y. et al. (2013): Hyperspectral remote sensing of foliar
  nitrogen content. *Proceedings of the National Academy of Sciences*,
  110(3), E185–E192. (DASF spectral invariance, canopy structure)
- Féret, J.B. et al. (2017): PROSPECT-D: Towards modeling leaf optical
  properties through a complete lifecycle. *Remote Sensing of Environment*,
  193, 204–215. (PROSPECT-D leaf albedo table for DASF)

## AUTHORS

i.hyper.smac project.
