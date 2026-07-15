# lib6sv — API Examples

Side-by-side C and Python examples covering every major feature of lib6sv.
Each section shows the same operation in both languages.

## Contents

| # | Example | Topics |
|---|---|---|
| 1 | [Basic LUT + correction](#1-lut-computation-and-single-pixel-correction) | LUT setup, `atcorr_lut_slice`, `atcorr_invert`, `sixs_E0`, `sixs_earth_sun_dist2` |
| 2 | [Scene-scale correction](#2-scene-scale-correction) | Per-pixel parallel loop, trilinear LUT interpolation, polarized RT, BRDF-coupled inversion |
| 3 | [Atmospheric retrievals](#3-atmospheric-state-retrievals) | Solar position, H₂O, AOD DDV + MAIAC, O₃, O₂-A pressure, quality mask, OE retrieval |
| 4 | [BRDF models](#4-brdf-surface-models) | RPV, Ross-Li, Hapke, white-sky albedo, NBAR, MCD43 disaggregation, Tikhonov smoothing |
| 5 | [Spatial, terrain, adjacency, uncertainty](#5-spatial-filters-terrain-adjacency-uncertainty) | Gaussian/box filter, terrain illumination, Vermote 1997, uncertainty propagation |
| 6 | [Full pipeline](#6-full-end-to-end-pipeline) | Everything wired together over a synthetic 32×32 hyperspectral scene |

## How to compile and run C examples

```sh
cd examples

# Build the standalone library first (one time)
cd ../testsuite && make lib && cd ../examples

# Compile all examples
make

# Run them all
make run

# Or compile and run a single example
make 01_basic_lut && ./01_basic_lut
```

## How to run Python examples

The Python examples are **fully standalone** — no GRASS GIS or `atcorr.py` wrapper
required.  They load `libsixsv.so` directly via `ctypes`.

```sh
# Build the library first (one time)
cd ../testsuite && make lib && cd ../examples

# Run any example
python3 01_basic_lut.py

# Run all Python examples
for f in 0?_*.py; do python3 "$f"; done

# Point to a custom library location
LIB_SIXSV=/path/to/libsixsv.so python3 01_basic_lut.py
```

The search order for the library is:
1. `$LIB_SIXSV` environment variable (if set and the file exists)
2. `../testsuite/libsixsv.so` relative to the script location

---

## Validation — Expected Outputs

All 12 examples (6 C + 6 Python) produce identical numeric results (confirmed
bit-for-bit for scalar outputs; float32 array means agree to the last printed
digit).  The C pipeline additionally applies a terrain correction step that the
Python pipeline replaces with a DASF canopy retrieval, so their `mean_BOA`
values legitimately differ in example 06.

### 01 — Basic LUT + single-pixel correction

```
LUT shape: R_atm (4, 3, 4)  (n_aod × n_h2o × n_wl)

Band       TOA     BOA   R_atm    T_dn    T_up   s_alb
------------------------------------------------------
Blue    0.1800  0.1329  0.0840  0.8418  0.8418  0.1434
Green   0.2000  0.1948  0.0395  0.9005  0.9005  0.0812
Red     0.1500  0.1590  0.0221  0.8900  0.8962  0.0545
NIR     0.3500  0.3730  0.0103  0.9478  0.9479  0.0365

Solar irradiance at 550 nm: 1871.1 W/m²/µm
Earth-Sun d² at DOY 185 (aphelion): 1.033697 AU²
```

### 02 — Scene-scale correction

```
LUT computed: R_atm (5, 4, 4)  (polarized RT enabled)
Band 0 Blue  (0.45 µm): mean BOA = -0.0486
Band 1 Green (0.55 µm): mean BOA =  0.0926
Band 2 Red   (0.65 µm): mean BOA =  0.1947
Band 3 NIR   (0.87 µm): mean BOA =  0.2556

RPV BRDF correction: rho_BRDF = 0.1702  (white-sky albedo = 0.2290)
```

> Blue band BOA is negative because the synthetic TOA is lower than R_atm
> for the chosen scene parameters — expected behaviour for a dark target.

### 03 — Atmospheric state retrievals

```
Surface pressure at 1500 m: 845.6 hPa

H₂O retrieval (940 nm): mean WVC = 1.53 g/cm²
AOD retrieval (DDV): scene mean = 0.150
AOD after MAIAC smoothing: mean = 0.150
O₃ column (Chappuis 600 nm): 300 DU
Quality mask: cloud=0  water=0  (of 1024 pixels)
OE retrieval: mean AOD = 0.148  mean H₂O = 1.00 g/cm²
```

### 04 — BRDF surface models

```
RPV:       rho = 0.2345   white-sky albedo = 0.2295
Ross-Li:   rho = 0.0706   white-sky albedo = 0.0692
Hapke:     rho = 0.2972

NBAR:  rho_boa = 0.2200  →  rho_NBAR = 0.2205  (VZA 8° → nadir)

MCD43 disaggregation: f_iso at selected wavelengths:
  0.40 µm: fiso=0.0775  fvol=0.0373  fgeo=0.0079
  0.80 µm: fiso=0.2339  fvol=0.0923  fgeo=0.0451
  1.20 µm: fiso=0.1405  fvol=0.0493  fgeo=0.0148
  ...

Smoothed spectrum: 0.0501  0.0696  0.0884  0.1078  0.1354  0.1871  0.2178  0.2337
```

### 05 — Spatial filters, terrain, adjacency, uncertainty

```
Gaussian filter: NaN before=41  after=0
Box filter (half=3): output mean = 0.1000

Terrain:  cos_i = 0.9396  skyview = 0.9698
T_down flat=0.8500  T_down_eff (slope)=0.9484
T_up flat=0.9000   T_up_eff (off-nadir view)=0.8976

Adjacency correction: mean BOA = 0.2230
Uncertainty (σ_rfl) at 650 nm: mean = 0.00531
```

### 06 — Full end-to-end pipeline

```
=== lib6sv Full Pipeline ===
Scene: 32×32 px  DOY=210  SZA=30.0°  VZA=6.0°

[1] Surface pressure: 920.8 hPa (800 m elevation)
[2] O₃ column: 354 DU
[3] H₂O: mean WVC = 1.89 g/cm²
[4] AOD: scene mean = 0.150 (after MAIAC)
[5] LUT computed: (5, 4, 10)
[6] Valid pixels: 1024 / 1024
[7] Per-pixel correction done (Lambertian)
[8] Adjacency correction done
[9] Uncertainty propagation done
[10] DASF: mean = 0.495  (canopy structure factor)

Band   WL(µm)   mean_BOA   mean_sigma
0      0.45     0.1085     0.00394
1      0.50     0.1367     0.00423
2      0.55     0.1356     0.00370
3      0.60     0.1468     0.00354
4      0.65     0.1410     0.00307
5      0.70     0.1405     0.00274
6      0.75     0.1274     0.00229
7      0.80     0.1332     0.00220
8      0.84     0.1460     0.00222
9      0.87     0.1301     0.00186
```

> The C pipeline applies a terrain correction at step 9 (slope=12°, aspect=200°)
> which scales BOA reflectances upward by ~10 %.  The Python pipeline skips
> terrain correction and instead demonstrates the DASF canopy retrieval at
> step 10.  All preceding steps (pressure, O₃, H₂O, AOD, LUT, mask,
> Lambertian inversion, adjacency, uncertainty) produce identical results.

---

## 1. LUT Computation and Single-Pixel Correction

Build the 3-D [AOD × H₂O × λ] look-up table, interpolate at a fixed atmospheric
state, then invert the 6SV forward model for each spectral band.

### C

```c
#include <stdio.h>
#include <stdlib.h>
#include "atcorr.h"

int main(void)
{
    float wl[]  = {0.45f, 0.55f, 0.65f, 0.87f};   /* µm */
    float aod[] = {0.0f, 0.1f, 0.2f, 0.4f};
    float h2o[] = {1.0f, 2.0f, 3.0f};
    int n_wl = 4, n_aod = 4, n_h2o = 3;
    int N = n_aod * n_h2o * n_wl;

    LutConfig cfg = {
        .wl  = wl,  .n_wl  = n_wl,
        .aod = aod, .n_aod = n_aod,
        .h2o = h2o, .n_h2o = n_h2o,
        .sza = 35.0f, .vza = 5.0f, .raa = 90.0f,
        .altitude_km   = 705.0f,   /* Landsat orbit */
        .atmo_model    = ATMO_US62,
        .aerosol_model = AEROSOL_CONTINENTAL,
        .ozone_du      = 300.0f,
    };

    /* Allocate LUT arrays (caller-owned) */
    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));

    LutArrays lut = {
        .R_atm = R_atm, .T_down = T_down,
        .T_up  = T_up,  .s_alb  = s_alb,
        .T_down_dir = NULL, .R_atmQ = NULL, .R_atmU = NULL,
    };

    /* OpenMP-parallel over the AOD dimension */
    atcorr_compute_lut(&cfg, &lut);

    /* Bilinear interpolation at (AOD=0.15, H₂O=2.0) → 1-D spectral arrays */
    float Rs[4], Tds[4], Tus[4], ss[4];
    atcorr_lut_slice(&cfg, &lut, 0.15f, 2.0f, Rs, Tds, Tus, ss, NULL);

    /* Lambertian BOA inversion — static inline, no function-call overhead */
    float rho_toa[] = {0.18f, 0.20f, 0.15f, 0.35f};
    for (int b = 0; b < n_wl; b++) {
        float rho_boa = atcorr_invert(rho_toa[b], Rs[b], Tds[b], Tus[b], ss[b]);
        printf("%.2f µm: TOA=%.4f  BOA=%.4f\n", wl[b], rho_toa[b], rho_boa);
    }

    /* Solar irradiance and Earth–Sun distance */
    printf("E0(0.55 µm) = %.1f W/m²/µm\n", sixs_E0(0.55f));
    printf("d²(DOY=185) = %.6f AU²\n", sixs_earth_sun_dist2(185));

    free(R_atm); free(T_down); free(T_up); free(s_alb);
}
```

### Python

```python
import numpy as np
import atcorr as ac

cfg = ac.LutConfig(
    wl  = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32),
    aod = np.array([0.0, 0.1, 0.2, 0.4],     dtype=np.float32),
    h2o = np.array([1.0, 2.0, 3.0],           dtype=np.float32),
    sza=35.0, vza=5.0, raa=90.0,
    altitude_km=705.0,
    atmo_model=1,        # ATMO_US62
    aerosol_model=1,     # AEROSOL_CONTINENTAL
    ozone_du=300.0,
)

# Arrays are allocated internally; returned as numpy views
lut = ac.compute_lut(cfg)            # LutArrays, shape [4, 3, 4]

# Bilinear slice → 1-D spectral arrays [n_wl]
sl = ac.lut_slice(cfg, lut, aod_val=0.15, h2o_val=2.0)

# Vectorised inversion — operates on entire band at once
rho_toa = np.array([0.18, 0.20, 0.15, 0.35], dtype=np.float32)
rho_boa = ac.invert(rho_toa, sl.R_atm, sl.T_down, sl.T_up, sl.s_alb)
for b, wl_b in enumerate([0.45, 0.55, 0.65, 0.87]):
    print(f"{wl_b:.2f} µm: TOA={rho_toa[b]:.4f}  BOA={rho_boa[b]:.4f}")

print(f"E0(0.55 µm) = {ac.solar_E0(0.55):.1f} W/m²/µm")
print(f"d²(DOY=185) = {ac.earth_sun_dist2(185):.6f} AU²")
```

---

## 2. Scene-Scale Correction

### Per-pixel trilinear interpolation from a spatially varying AOD/H₂O map

#### C

```c
/* Spatially varying AOD map — trilinear per-pixel LUT lookup */
#pragma omp parallel for schedule(static)
for (int i = 0; i < npix; i++) {
    float Ra, Td, Tu, sa;
    atcorr_lut_interp_pixel(&cfg, &lut,
                            aod_map[i], h2o_map[i], wl[b],
                            &Ra, &Td, &Tu, &sa);
    rho_boa[b * npix + i] = atcorr_invert(rho_toa[b * npix + i],
                                           Ra, Td, Tu, sa);
}
```

#### Python

```python
# lut_slice() with per-pixel aod/h2o is available via the C function;
# for the common case of a scene-average atmosphere, lut_slice() is fastest:
sl = ac.lut_slice(cfg, lut, aod_val=float(aod_map.mean()),
                  h2o_val=float(h2o_map.mean()))
rho_boa = ac.invert(rho_toa, sl.R_atm[b], sl.T_down[b],
                    sl.T_up[b], sl.s_alb[b])   # vectorised over all pixels
```

### Polarized RT (Stokes I/Q/U — improves R_atm in blue by 1–5 %)

#### C

```c
LutConfig cfg = {
    /* ... */
    .enable_polar = 1,   /* scalar: 0 (default)  |  vector: 1 */
};

/* Allocate Q and U Stokes arrays */
float *R_atmQ = malloc(N * sizeof(float));
float *R_atmU = malloc(N * sizeof(float));
LutArrays lut = {
    .R_atm = R_atm, .T_down = T_down, .T_up = T_up, .s_alb = s_alb,
    .R_atmQ = R_atmQ, .R_atmU = R_atmU,
};
atcorr_compute_lut(&cfg, &lut);
/* lut.R_atmQ and lut.R_atmU are now populated */
```

#### Python

```python
cfg = ac.LutConfig(
    # ...
    enable_polar=1,   # 0 = scalar RT (default), 1 = Stokes I/Q/U
)
lut = ac.compute_lut(cfg)
print(lut.R_atmQ is not None)   # True — Q Stokes component available
```

### BRDF-coupled inversion (white-sky albedo feedback)

#### C

```c
#include "brdf.h"

/* RPV model parameters */
BrdfParams rpv = { .rahman = { .rho0 = 0.12f, .af = -0.15f, .k = 0.75f } };
float cos_sza  = cosf(cfg.sza * M_PI / 180.0f);

/* White-sky albedo by numerical hemisphere integration */
float rho_albe = sixs_brdf_albe(BRDF_RAHMAN, &rpv, cos_sza, 48, 24);

/* BRDF-coupled inversion (replaces the Lambertian s·ρ denominator) */
float rho_brdf = atcorr_invert_brdf(rho_toa, Ra, Td, Tu, sa, rho_albe);
```

#### Python

```python
import ctypes, math

# sixs_brdf_albe: brdf_type=1 (RPV), params = (rho0, af, k, 0, 0)
rpv_params = (ctypes.c_float * 5)(0.12, -0.15, 0.75, 0.0, 0.0)
ac._lib.sixs_brdf_albe.restype = ctypes.c_float
rho_albe = ac._lib.sixs_brdf_albe(
    1, rpv_params,
    ctypes.c_float(math.cos(math.radians(35.0))),
    ctypes.c_int(48), ctypes.c_int(24))

# Lambertian ac.invert() + white-sky coupling: formula equivalent to atcorr_invert_brdf()
y = (rho_toa - R_atm) / (T_down * T_up + 1e-10)
rho_brdf = y * (1.0 - s_alb * rho_albe)
```

---

## 3. Atmospheric State Retrievals

### Solar position

#### C

```c
#include "atcorr.h"

float sol_zen, sol_az;
sixs_possol(/*month*/7, /*day*/4, /*UTC*/10.5f,
            /*lon*/-122.0f, /*lat*/37.5f,
            &sol_zen, &sol_az, /*year*/2024);
printf("SZA = %.2f°  SAA = %.2f°\n", sol_zen, sol_az);
```

#### Python

```python
import ctypes
ac._lib.sixs_possol.argtypes = [
    ctypes.c_int, ctypes.c_int, ctypes.c_float,
    ctypes.c_float, ctypes.c_float,
    ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
    ctypes.c_int,
]
ac._lib.sixs_possol.restype = None
sol_zen = ctypes.c_float(); sol_az = ctypes.c_float()
ac._lib.sixs_possol(7, 4, ctypes.c_float(10.5),
                    ctypes.c_float(-122.0), ctypes.c_float(37.5),
                    ctypes.byref(sol_zen), ctypes.byref(sol_az), 2024)
print(f"SZA = {sol_zen.value:.2f}°  SAA = {sol_az.value:.2f}°")
```

### Surface pressure

#### C

```c
#include "retrieve.h"
float p = retrieve_pressure_isa(1500.0f);   /* 1500 m elevation → hPa */
```

#### Python

```python
p = ac.retrieve_pressure_isa(1500.0)        # float → hPa
```

### H₂O column from 940 nm band depth (Kaufman & Gao 1992)

#### C

```c
float *wvc = malloc(npix * sizeof(float));
retrieve_h2o_940(L_865, L_940, L_1040,
                 /*fwhm_um=*/0.0f,   /* 0 = MODIS broadband K */
                 npix, sza_deg, vza_deg, wvc);
```

#### Python

```python
wvc = ac.retrieve_h2o_940(L_865, L_940, L_1040,
                           sza_deg=35.0, vza_deg=5.0,
                           fwhm_um=0.0)   # numpy array [npix]
```

For narrow-band sensors, pass the actual FWHM of your 940 nm band
(e.g. `fwhm_um=0.007` for a 7 nm FWHM channel) and the absorption coefficient
is automatically scaled by the Kaufman–Gao power law.

### H₂O from a generic absorption triplet

#### C

```c
uint8_t *valid = malloc(npix);
retrieve_h2o_triplet(L_lo, L_feat, L_hi,
                     wl_lo_um, wl_feat_um, wl_hi_um,
                     /*K_ref=*/0.036f, /*fwhm_ref_um=*/0.050f,
                     /*fwhm_um=*/0.007f,
                     /*D_min=*/0.02f, /*D_max=*/0.80f,
                     npix, sza_deg, vza_deg,
                     wvc, valid);
```

#### Python

```python
wvc, valid = ac.retrieve_h2o_triplet(
    L_lo, L_feat, L_hi,
    wl_lo_um=0.865, wl_feat_um=0.940, wl_hi_um=1.040,
    K_ref=0.036, fwhm_ref_um=0.050, fwhm_um=0.007,
    D_min=0.02, D_max=0.80,
    sza_deg=35.0, vza_deg=5.0)
```

### AOD from MODIS DDV + MAIAC spatial smoothing

#### C

```c
float *aod_px = malloc(npix * sizeof(float));
float aod_scene = retrieve_aod_ddv(L_470, L_660, L_860, L_2130,
                                   npix, doy, sza_deg, aod_px);
retrieve_aod_maiac(aod_px, nrows, ncols, /*patch_sz=*/32);
```

#### Python

```python
aod_scene, aod_px = ac.retrieve_aod_ddv(L_470, L_660, L_860, L_2130,
                                          doy=185, sza_deg=35.0)
aod_2d = aod_px.reshape(nrows, ncols)
ac.retrieve_aod_maiac(aod_2d, patch_sz=32)   # in-place patch-median
```

### O₃ from Chappuis 600 nm

#### C

```c
float o3_du = retrieve_o3_chappuis(L_540, L_600, L_680,
                                    npix, sza_deg, vza_deg);
```

#### Python

```python
o3_du = ac.retrieve_o3_chappuis(L_540, L_600, L_680,
                                  sza_deg=35.0, vza_deg=5.0)
```

### Surface pressure from O₂-A band depth

#### C

```c
float *pressure_px = malloc(npix * sizeof(float));
retrieve_pressure_o2a(L_740, L_760, L_780, npix,
                      sza_deg, vza_deg, pressure_px);
```

#### Python

```python
pressure_px = ac.retrieve_pressure_o2a(L_740, L_760, L_780,
                                        sza_deg=35.0, vza_deg=5.0)
```

### Quality bitmask (cloud / shadow / water / snow)

#### C

```c
uint8_t *mask = malloc(npix);
retrieve_quality_mask(L_blue, L_red, L_nir,
                      /*L_swir=*/L_1600,   /* NULL → skip snow */
                      npix, doy, sza_deg, mask);

/* Test individual bits */
if (mask[i] & RETRIEVE_MASK_CLOUD)  { /* cloud */ }
if (mask[i] & RETRIEVE_MASK_SHADOW) { /* shadow */ }
if (mask[i] & RETRIEVE_MASK_WATER)  { /* water */ }
if (mask[i] & RETRIEVE_MASK_SNOW)   { /* snow / ice */ }
```

#### Python

```python
mask = ac.retrieve_quality_mask(L_blue, L_red, L_nir,
                                  doy=185, sza_deg=35.0,
                                  L_swir=L_1600)   # None → skip snow
cloud  = mask & ac.MASK_CLOUD   != 0
shadow = mask & ac.MASK_SHADOW  != 0
water  = mask & ac.MASK_WATER   != 0
snow   = mask & ac.MASK_SNOW    != 0
```

### Joint AOD + H₂O optimal estimation (ISOFIT-inspired)

#### C

```c
#include "oe_invert.h"

float out_aod[npix], out_h2o[npix];
oe_invert_aod_h2o(
    &cfg, &lut,
    rho_toa_vis,     /* [npix × n_vis], band-interleaved */
    npix, n_vis, vis_wl,
    L_865, L_940, L_1040,   /* H₂O consistency term; NULL to disable */
    sza_deg, vza_deg,
    /*aod_prior=*/0.15f,  /*h2o_prior=*/2.0f,
    /*sigma_aod=*/0.5f,   /*sigma_h2o=*/1.0f,
    /*sigma_spec=*/0.01f, /*fwhm_940_um=*/0.0f,
    out_aod, out_h2o);
```

#### Python

```python
out_aod, out_h2o = ac.oe_invert_aod_h2o(
    cfg, lut,
    rho_toa_vis=rho_vis,     # ndarray [npix, n_vis]
    vis_wl=np.array([0.47, 0.55, 0.66, 0.87], dtype=np.float32),
    L_865=L_865, L_940=L_940, L_1040=L_1040,
    sza_deg=35.0, vza_deg=5.0,
    aod_prior=0.15, h2o_prior=2.0,
    sigma_aod=0.5, sigma_h2o=1.0,
    sigma_spec=0.01, fwhm_940_um=0.0,
)
```

---

## 4. BRDF Surface Models

### Evaluate a BRDF at a single geometry point

#### C

```c
#include "brdf.h"

float cos_sza = cosf(35.0f * M_PI / 180.0f);
float cos_vza = cosf( 8.0f * M_PI / 180.0f);

/* RPV */
BrdfParams rpv = { .rahman = { .rho0=0.12f, .af=-0.15f, .k=0.75f } };
float rho_rpv = sixs_brdf_eval(BRDF_RAHMAN, &rpv, cos_sza, cos_vza, 90.0f);

/* Ross-Thick + Li-Sparse (MCD43 kernels) */
BrdfParams rl = { .rosslimaignan = { .f_iso=0.0774f, .f_vol=0.0372f, .f_geo=0.0079f } };
float rho_rl = sixs_brdf_eval(BRDF_ROSSLIMAIGNAN, &rl, cos_sza, cos_vza, 90.0f);

/* Ocean surface (Cox-Munk sun glint) */
BrdfParams ocean = { .ocean = { .wspd=7.0f, .azw=0.0f, .sal=35.0f,
                                 .pcl=0.1f,  .wl=0.55f } };
float rho_ocean = sixs_brdf_eval(BRDF_OCEAN, &ocean, cos_sza, cos_vza, 90.0f);
```

#### Python

```python
import ctypes, math
lib = ac._lib
lib.sixs_brdf_eval.argtypes = [ctypes.c_int,
                                ctypes.POINTER(ctypes.c_float),
                                ctypes.c_float, ctypes.c_float, ctypes.c_float]
lib.sixs_brdf_eval.restype  = ctypes.c_float

cos_sza = math.cos(math.radians(35.0))
cos_vza = math.cos(math.radians(8.0))

# RPV (type=1)
rpv = (ctypes.c_float * 5)(0.12, -0.15, 0.75, 0, 0)
rho_rpv = lib.sixs_brdf_eval(1, rpv,
    ctypes.c_float(cos_sza), ctypes.c_float(cos_vza), ctypes.c_float(90.0))

# Ross-Li (type=9)
rl = (ctypes.c_float * 5)(0.0774, 0.0372, 0.0079, 0, 0)
rho_rl = lib.sixs_brdf_eval(9, rl,
    ctypes.c_float(cos_sza), ctypes.c_float(cos_vza), ctypes.c_float(90.0))
```

### NBAR normalisation

#### C

```c
float rho_nbar = atcorr_brdf_normalize(
    rho_boa,
    f_iso, f_vol, f_geo,
    sza_obs, vza_obs, raa_obs,
    sza_nbar);   /* reference SZA for NBAR output */
```

#### Python

```python
ac._lib.atcorr_brdf_normalize.argtypes = [ctypes.c_float] * 8
ac._lib.atcorr_brdf_normalize.restype  = ctypes.c_float
rho_nbar = ac._lib.atcorr_brdf_normalize(
    ctypes.c_float(rho_boa),
    ctypes.c_float(f_iso), ctypes.c_float(f_vol), ctypes.c_float(f_geo),
    ctypes.c_float(sza_obs), ctypes.c_float(vza_obs), ctypes.c_float(raa_obs),
    ctypes.c_float(sza_nbar))
```

### MCD43 7-band → hyperspectral kernel weight disaggregation

#### C

```c
#include "spectral_brdf.h"

float fiso_hs[n_tgt], fvol_hs[n_tgt], fgeo_hs[n_tgt];
mcd43_disaggregate(fiso_7, fvol_7, fgeo_7,
                   wl_tgt, n_tgt,
                   /*alpha=*/0.10f,    /* Tikhonov smoothing weight */
                   fiso_hs, fvol_hs, fgeo_hs);
```

#### Python

```python
fiso_hs, fvol_hs, fgeo_hs = ac.mcd43_disaggregate(
    fiso_7, fvol_7, fgeo_7,
    wl_target=wl_tgt,
    alpha=0.10)   # Tikhonov smoothing
```

### Tikhonov spectral smoothing

#### C

```c
spectral_smooth_tikhonov(spectrum, n_bands, /*alpha=*/0.5f);   /* in-place */
```

#### Python

```python
smoothed = ac.spectral_smooth_tikhonov(spectrum, alpha=0.5)  # returns copy
```

---

## 5. Spatial Filters, Terrain, Adjacency, Uncertainty

### Gaussian and box spatial filters

Both functions are NaN-safe (NaN pixels are excluded from neighbourhood averages)
and use OpenMP parallelism with optional GPU offload (see `INSTALL.md`).

#### C

```c
#include "spatial.h"

/* Gaussian — in-place, σ in pixels */
spatial_gaussian_filter(aod_map, nrows, ncols, /*sigma=*/2.5f);

/* Box — writes to separate output (no aliasing allowed) */
float *aod_box = malloc(npix * sizeof(float));
spatial_box_filter(aod_map, aod_box, nrows, ncols, /*filter_half=*/3);
```

#### Python

```python
# Gaussian — in-place on a 2-D array
aod_2d = aod_map.reshape(nrows, ncols)
ac.spatial_gaussian_filter(aod_2d, sigma=2.5)   # modifies in-place

# Box — returns new array
aod_box = ac.spatial_box_filter(aod_2d, filter_half=3)
```

### Terrain illumination and transmittance correction (Proy 1989)

#### C

```c
#include "terrain.h"

float cos_i   = cos_incidence(sza_deg, saa_deg, slope_deg, aspect_deg);
float V_d     = skyview_factor(slope_deg);
float cos_sza = cosf(sza_deg * M_PI / 180.0f);

/* Topographic shadow: cos_i <= 0 */
float T_eff = atcorr_terrain_T_down(T_down, T_down_dir, cos_sza, cos_i, V_d);

/* View-zenith variation on tilted terrain */
float T_up_eff = atcorr_terrain_T_up(T_up, cos_vza_ref, vza_pixel_deg);
```

#### Python

```python
import ctypes, math
lib = ac._lib
lib.cos_incidence.restype   = ctypes.c_float
lib.skyview_factor.restype  = ctypes.c_float
lib.atcorr_terrain_T_down.restype = ctypes.c_float
lib.atcorr_terrain_T_up.restype   = ctypes.c_float

cos_i = lib.cos_incidence(
    ctypes.c_float(sza), ctypes.c_float(saa),
    ctypes.c_float(slope), ctypes.c_float(aspect))
V_d   = lib.skyview_factor(ctypes.c_float(slope))

T_eff = lib.atcorr_terrain_T_down(
    ctypes.c_float(T_down), ctypes.c_float(T_down_dir),
    ctypes.c_float(math.cos(math.radians(sza))),
    ctypes.c_float(cos_i), ctypes.c_float(V_d))

T_up_eff = lib.atcorr_terrain_T_up(
    ctypes.c_float(T_up),
    ctypes.c_float(math.cos(math.radians(vza_ref))),
    ctypes.c_float(vza_pixel_deg))
```

### Adjacency effect correction (Vermote 1997)

#### C

```c
#include "adjacency.h"

/* One call handles r_env box filter + T_dir computation + in-place correction */
adjacency_correct_band(
    r_boa, nrows, ncols,
    /*psf_radius_km=*/1.0f,
    /*pixel_size_m=*/30.0f,         /* Landsat 30 m */
    /*T_scat=*/1.0f - T_down_dir,   /* scattering (diffuse) transmittance */
    /*s_alb=*/0.08f,
    /*wl_um=*/0.65f,
    /*aod550=*/0.15f,
    /*pressure=*/1013.25f,
    sza_deg, vza_deg);
```

#### Python

```python
import ctypes
lib = ac._lib
lib.adjacency_correct_band.restype = None
ptr = r_boa_2d.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
lib.adjacency_correct_band(
    ptr, ctypes.c_int(nrows), ctypes.c_int(ncols),
    ctypes.c_float(1.0),   ctypes.c_float(30.0),
    ctypes.c_float(T_scat), ctypes.c_float(s_alb),
    ctypes.c_float(0.65),  ctypes.c_float(0.15),
    ctypes.c_float(1013.25), ctypes.c_float(sza), ctypes.c_float(vza))
```

### Uncertainty propagation (noise + AOD in quadrature)

#### C

```c
#include "uncertainty.h"

float *sigma = malloc(npix * sizeof(float));
uncertainty_compute_band(
    rad_band, refl_band, npix,
    E0, d2, cos_sza,
    T_down, T_up, s_alb, R_atm,
    /*nedl=*/0.0f,       /* 0 → estimate from darkest 5% of rad_band */
    /*aod_sigma=*/0.04f,
    &cfg, &lut,
    wl_um, aod_val, h2o_val,
    sigma);
```

#### Python

```python
sigma = ac.uncertainty_compute_band(
    rad_band=rad_band,   # None → use NEDL fallback 0.01
    refl_band=refl_band,
    E0=E0, d2=d2, cos_sza=cos_sza,
    T_down=T_down, T_up=T_up, s_alb=s_alb, R_atm=R_atm,
    nedl=0.0, aod_sigma=0.04,
    cfg=cfg, lut=lut,
    wl_um=0.65, aod_val=0.15, h2o_val=2.0)
```

---

## 6. Full End-to-End Pipeline

The files `06_full_pipeline.c` and `06_full_pipeline.py` wire together all of
the above into a complete 10-step processing chain over a synthetic 32×32 scene:

```
pressure ← ISA(elevation)
O₃        ← Chappuis band depth
H₂O map   ← 940 nm band depth + Gaussian smooth
AOD map   ← DDV + MAIAC patch-median
LUT       ← atcorr_compute_lut (OpenMP-parallel)
mask      ← cloud/shadow/water/snow bitmask
rho_boa   ← Lambertian inversion per pixel, valid pixels only
           ← Adjacency correction (Vermote 1997)
           ← Terrain illumination correction (Proy 1989)
sigma_rfl ← Uncertainty (noise ⊕ AOD) per band
DASF      ← Canopy structure from 710–790 nm NIR plateau
```

Run:
```sh
# C
make 06_full_pipeline && ./06_full_pipeline

# Python
python3 06_full_pipeline.py
```

---

## Pleiades Neo — VHR 6-band multispectral (1.2 m GSD)

Pleiades Neo has no dedicated water-vapour or SWIR band, so H₂O defaults to a
NWP-provided value and snow detection is skipped.  At 1.2 m GSD the adjacency
effect is significant even at low AOD — use a small PSF radius.

| Band | Name       | Centre (µm) | FWHM (nm) |
|------|------------|-------------|-----------|
| 0    | Deep Blue  |   0.425     |    50     |
| 1    | Blue       |   0.490     |    70     |
| 2    | Green      |   0.560     |    60     |
| 3    | Red        |   0.655     |    75     |
| 4    | Red Edge   |   0.718     |    43     |
| 5    | NIR        |   0.790     |    85     |

### C + OpenMP

```c
#include <stdlib.h>
#include <math.h>
#include "atcorr.h"
#include "retrieve.h"
#include "adjacency.h"

/* Band centres [µm]: Deep-Blue  Blue   Green   Red   Red-Edge   NIR */
static const float WL_PLN[6] = { 0.425f, 0.490f, 0.560f,
                                  0.655f, 0.718f, 0.790f };

void correct_pleiades_neo(
    /* TOA reflectance (6 bands, each nrows×ncols, band-major flat arrays) */
    float *toa[6], float *boa[6],
    int nrows, int ncols,
    float sza_deg, float vza_deg, float raa_deg,
    int doy, float elev_m,
    float h2o_g_cm2)      /* from NWP/MODIS MOD05; default 1.5 */
{
    int npix = nrows * ncols;

    /* 1. Surface pressure from scene mean elevation */
    float pressure = retrieve_pressure_isa(elev_m);

    /* 2. O₃ from Chappuis (Green ≈ 560 nm ≈ "600 nm" feature) */
    float o3_du = retrieve_o3_chappuis(
        toa[2], toa[3], toa[4],       /* 560 nm / 655 nm / 718 nm */
        npix, sza_deg, vza_deg);

    /* 3. AOD — Pleiades Neo has no 2130 nm band.
     *    Proxy SWIR from the NIR band: ρ_2130 ≈ ρ_NIR × 0.25
     *    (conservative; leads to fallback 0.15 in low-vegetation scenes). */
    float *swir_proxy = malloc(npix * sizeof(float));
    for (int i = 0; i < npix; i++) swir_proxy[i] = toa[5][i] * 0.25f;

    float *aod_px = malloc(npix * sizeof(float));
    float aod_scene = retrieve_aod_ddv(
        toa[1], toa[3], toa[5], swir_proxy,
        npix, doy, sza_deg, aod_px);
    free(swir_proxy);

    /* MAIAC patch-median: 64 px × 1.2 m ≈ 77 m blocks */
    retrieve_aod_maiac(aod_px, nrows, ncols, /*patch_sz=*/64);

    /* 4. Build 3-D LUT (OpenMP-parallel over AOD nodes) */
    float aod_grid[] = { 0.0f, 0.05f, 0.10f, 0.20f, 0.40f };
    float h2o_grid[] = { 0.5f, 1.0f,  1.5f,  2.5f,  3.5f  };
    int N = 5 * 5 * 6;
    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));

    LutConfig cfg = {
        .wl  = (float *)WL_PLN, .n_wl  = 6,
        .aod = aod_grid,        .n_aod = 5,
        .h2o = h2o_grid,        .n_h2o = 5,
        .sza = sza_deg, .vza = vza_deg, .raa = raa_deg,
        .altitude_km      = 1000.0f,       /* analytical Rayleigh path */
        .atmo_model       = ATMO_US62,
        .aerosol_model    = AEROSOL_CONTINENTAL,
        .surface_pressure = pressure,
        .ozone_du         = o3_du,
    };
    LutArrays lut = { .R_atm  = R_atm,  .T_down = T_down,
                      .T_up   = T_up,   .s_alb  = s_alb  };
    atcorr_compute_lut(&cfg, &lut);   /* OpenMP: parallel over AOD */

    /* 5. Quality mask — no SWIR so snow bit is always clear */
    uint8_t *mask = malloc(npix);
    retrieve_quality_mask(toa[1], toa[3], toa[5], /*L_swir=*/NULL,
                          npix, doy, sza_deg, mask);

    /* 6. Per-pixel Lambertian inversion + adjacency correction (1.2 m) */
    for (int b = 0; b < 6; b++) {
        #pragma omp parallel for schedule(static)
        for (int i = 0; i < npix; i++) {
            if (mask[i]) { boa[b][i] = 0.0f; continue; }
            float Ra, Td, Tu, sa;
            atcorr_lut_interp_pixel(&cfg, &lut,
                                    aod_px[i], h2o_g_cm2, WL_PLN[b],
                                    &Ra, &Td, &Tu, &sa);
            boa[b][i] = atcorr_invert(toa[b][i], Ra, Td, Tu, sa);
        }
        /* PSF radius 0.5 km at 1.2 m GSD — accounts for urban haze halo */
        float Rs[6], Tds[6], Tus[6], ss[6];
        atcorr_lut_slice(&cfg, &lut, aod_scene, h2o_g_cm2,
                         Rs, Tds, Tus, ss, NULL);
        adjacency_correct_band(
            boa[b], nrows, ncols,
            /*psf_radius_km=*/0.5f, /*pixel_size_m=*/1.2f,
            /*T_scat=*/1.0f - Tds[b],
            /*s_alb=*/ss[b], WL_PLN[b],
            aod_scene, pressure, sza_deg, vza_deg);
    }

    free(aod_px); free(mask);
    free(R_atm); free(T_down); free(T_up); free(s_alb);
}
```

### Python

```python
import os, ctypes, math
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
for _p in [os.environ.get("LIB_SIXSV", ""),
           os.path.join(_here, "..", "testsuite", "libsixsv.so")]:
    if _p and os.path.exists(_p):
        _lib = ctypes.CDLL(_p); break
else:
    raise ImportError("libsixsv.so not found")

_FP = ctypes.POINTER(ctypes.c_float)
def _fp(a): return np.ascontiguousarray(a, dtype=np.float32).ctypes.data_as(_FP)

# Pleiades Neo band centres [µm]
WL_PLN = np.array([0.425, 0.490, 0.560, 0.655, 0.718, 0.790], dtype=np.float32)

def correct_pleiades_neo(toa, nrows, ncols,
                          sza_deg, vza_deg, raa_deg,
                          doy, elev_m, h2o_g_cm2=1.5):
    """
    toa : ndarray [6, nrows*ncols] — TOA reflectance
    Returns boa : ndarray [6, nrows*ncols]
    """
    npix = nrows * ncols

    # 1. Surface pressure
    _lib.retrieve_pressure_isa.argtypes = [ctypes.c_float]
    _lib.retrieve_pressure_isa.restype  = ctypes.c_float
    pressure = float(_lib.retrieve_pressure_isa(ctypes.c_float(elev_m)))

    # 2. O₃ from Chappuis (Green / Red / Red-Edge as 540/600/680 nm proxies)
    _lib.retrieve_o3_chappuis.argtypes = [
        _FP, _FP, _FP, ctypes.c_int, ctypes.c_float, ctypes.c_float]
    _lib.retrieve_o3_chappuis.restype = ctypes.c_float
    o3_du = float(_lib.retrieve_o3_chappuis(
        _fp(toa[2]), _fp(toa[3]), _fp(toa[4]),
        ctypes.c_int(npix),
        ctypes.c_float(sza_deg), ctypes.c_float(vza_deg)))

    # 3. AOD — proxy SWIR from NIR (no 2130 nm band on Pleiades Neo)
    swir_proxy = (toa[5] * 0.25).astype(np.float32)
    _lib.retrieve_aod_ddv.argtypes = [
        _FP, _FP, _FP, _FP, ctypes.c_int, ctypes.c_int, ctypes.c_float, _FP]
    _lib.retrieve_aod_ddv.restype = ctypes.c_float
    aod_px = np.empty(npix, np.float32)
    aod_scene = float(_lib.retrieve_aod_ddv(
        _fp(toa[1]), _fp(toa[3]), _fp(toa[5]), _fp(swir_proxy),
        ctypes.c_int(npix), ctypes.c_int(doy),
        ctypes.c_float(sza_deg), _fp(aod_px)))

    _lib.retrieve_aod_maiac.argtypes = [_FP, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    _lib.retrieve_aod_maiac.restype  = None
    aod_2d = np.ascontiguousarray(aod_px.reshape(nrows, ncols))
    _lib.retrieve_aod_maiac(aod_2d.ctypes.data_as(_FP),
                             ctypes.c_int(nrows), ctypes.c_int(ncols),
                             ctypes.c_int(64))      # 64 px × 1.2 m ≈ 77 m blocks

    # 4. LUT
    wl_  = WL_PLN
    aod_ = np.array([0.0, 0.05, 0.10, 0.20, 0.40], dtype=np.float32)
    h2o_ = np.array([0.5, 1.0,  1.5,  2.5,  3.5 ], dtype=np.float32)
    N = wl_.size * aod_.size * h2o_.size
    Ra, Td, Tu, ss = [np.empty(N, np.float32) for _ in range(4)]

    class _Cfg(ctypes.Structure):
        _fields_ = [
            ("wl",_FP),("n_wl",ctypes.c_int),("aod",_FP),("n_aod",ctypes.c_int),
            ("h2o",_FP),("n_h2o",ctypes.c_int),
            ("sza",ctypes.c_float),("vza",ctypes.c_float),("raa",ctypes.c_float),
            ("altitude_km",ctypes.c_float),("atmo_model",ctypes.c_int),
            ("aerosol_model",ctypes.c_int),("surface_pressure",ctypes.c_float),
            ("ozone_du",ctypes.c_float),
            ("mie_r_mode",ctypes.c_float),("mie_sigma_g",ctypes.c_float),
            ("mie_m_real",ctypes.c_float),("mie_m_imag",ctypes.c_float),
            ("brdf_type",ctypes.c_int),("brdf_params",ctypes.c_float*5),
            ("enable_polar",ctypes.c_int),
        ]
    class _Arr(ctypes.Structure):
        _fields_ = [("R_atm",_FP),("T_down",_FP),("T_up",_FP),("s_alb",_FP),
                    ("T_down_dir",_FP),("R_atmQ",_FP),("R_atmU",_FP)]

    cfg_c = _Cfg(wl=_fp(wl_),n_wl=wl_.size,aod=_fp(aod_),n_aod=aod_.size,
                 h2o=_fp(h2o_),n_h2o=h2o_.size,
                 sza=sza_deg,vza=vza_deg,raa=raa_deg,altitude_km=1000.,
                 atmo_model=1,aerosol_model=1,
                 surface_pressure=pressure,ozone_du=o3_du)
    arr_c = _Arr(R_atm=_fp(Ra),T_down=_fp(Td),T_up=_fp(Tu),s_alb=_fp(ss))
    _lib.atcorr_compute_lut(ctypes.byref(cfg_c), ctypes.byref(arr_c))

    lut = dict(cfg_c=cfg_c, arr_c=arr_c,
               wl=wl_, aod=aod_, h2o=h2o_,
               _Ra=Ra, _Td=Td, _Tu=Tu, _ss=ss)

    # 5. Quality mask (no SWIR → no snow bit)
    mask = np.zeros(npix, dtype=np.uint8)
    _lib.retrieve_quality_mask.argtypes = [
        _FP, _FP, _FP, _FP, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.POINTER(ctypes.c_uint8)]
    _lib.retrieve_quality_mask.restype = None
    _lib.retrieve_quality_mask(
        _fp(toa[1]), _fp(toa[3]), _fp(toa[5]), None,
        ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza_deg),
        mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))

    # 6. Per-pixel inversion + adjacency correction
    _lib.atcorr_lut_slice.argtypes = [
        ctypes.POINTER(_Cfg), ctypes.POINTER(_Arr),
        ctypes.c_float, ctypes.c_float, _FP, _FP, _FP, _FP, _FP]
    _lib.atcorr_lut_slice.restype = None

    _lib.adjacency_correct_band.argtypes = [
        _FP, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float]
    _lib.adjacency_correct_band.restype = None

    _lib.atcorr_lut_interp_pixel.argtypes = [
        ctypes.POINTER(_Cfg), ctypes.POINTER(_Arr),
        ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float),
        ctypes.POINTER(ctypes.c_float), ctypes.POINTER(ctypes.c_float)]
    _lib.atcorr_lut_interp_pixel.restype = None

    boa = np.zeros_like(toa)
    Rs = np.empty(wl_.size, np.float32)
    Tds = np.empty(wl_.size, np.float32)
    Tus = np.empty(wl_.size, np.float32)
    sas = np.empty(wl_.size, np.float32)
    _lib.atcorr_lut_slice(ctypes.byref(cfg_c), ctypes.byref(arr_c),
                          ctypes.c_float(aod_scene), ctypes.c_float(h2o_g_cm2),
                          _fp(Rs), _fp(Tds), _fp(Tus), _fp(sas), None)

    for b in range(6):
        Ra_b = np.empty(npix, np.float32)
        Td_b = np.empty(npix, np.float32)
        Tu_b = np.empty(npix, np.float32)
        sa_b = np.empty(npix, np.float32)
        for i in range(npix):
            if mask[i]: continue
            _Ra = ctypes.c_float(); _Td = ctypes.c_float()
            _Tu = ctypes.c_float(); _sa = ctypes.c_float()
            _lib.atcorr_lut_interp_pixel(
                ctypes.byref(cfg_c), ctypes.byref(arr_c),
                ctypes.c_float(float(aod_2d.ravel()[i])),
                ctypes.c_float(h2o_g_cm2), ctypes.c_float(float(WL_PLN[b])),
                ctypes.byref(_Ra), ctypes.byref(_Td),
                ctypes.byref(_Tu), ctypes.byref(_sa))
            Ra_b[i]=_Ra.value; Td_b[i]=_Td.value
            Tu_b[i]=_Tu.value; sa_b[i]=_sa.value

        boa_b = ((toa[b] - Ra_b) / (Td_b * Tu_b + 1e-10)).astype(np.float32)
        boa_b /= (1.0 + sa_b * boa_b)
        boa_b[mask != 0] = 0.0
        boa[b] = boa_b.ravel()

        band_2d = np.ascontiguousarray(boa[b].reshape(nrows, ncols))
        T_scat  = float(1.0 - Tds[b])
        _lib.adjacency_correct_band(
            band_2d.ctypes.data_as(_FP),
            ctypes.c_int(nrows), ctypes.c_int(ncols),
            ctypes.c_float(0.5),  ctypes.c_float(1.2),   # PSF 0.5 km, 1.2 m GSD
            ctypes.c_float(T_scat), ctypes.c_float(float(sas[b])),
            ctypes.c_float(float(WL_PLN[b])),
            ctypes.c_float(aod_scene), ctypes.c_float(pressure),
            ctypes.c_float(sza_deg), ctypes.c_float(vza_deg))
        boa[b] = band_2d.ravel()

    return boa
```

---

## EnMAP — Hyperspectral VNIR+SWIR (30 m, ~224 bands, 6.5 nm FWHM)

EnMAP's narrow 6.5 nm FWHM substantially increases the effective H₂O absorption
coefficient at 940 nm compared with broadband sensors — the Kaufman–Gao power
law scales `K₉₄₀` from 0.036 (50 nm MODIS reference) to ~0.22 at 6.5 nm.
Water-vapour absorption bands at 1380 nm and 1900 nm require masking or
gap-filling in SWIR before processing.

| Range  | Bands | Sampling | FWHM  | Centre range |
|--------|-------|----------|-------|--------------|
| VNIR   |  96   | 6.5 nm   | 6.5 nm | 420–1000 nm |
| SWIR   | 128   | 6.5 nm   | 6.5 nm | 900–2450 nm |

### C + OpenMP

```c
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "atcorr.h"
#include "retrieve.h"
#include "adjacency.h"
#include "spectral_brdf.h"

#define N_VNIR 96

/* Generate EnMAP VNIR wavelength grid: 420–1000 nm at 6.0 nm steps */
static void enmap_vnir_wl(float *wl) {
    for (int i = 0; i < N_VNIR; i++)
        wl[i] = 0.420f + i * (1.000f - 0.420f) / (N_VNIR - 1);
}

void correct_enmap_vnir(
    float *toa,        /* [N_VNIR × npix] band-major TOA reflectance */
    float *boa,        /* [N_VNIR × npix] output BOA reflectance      */
    int nrows, int ncols,
    float sza_deg, float vza_deg, float raa_deg,
    int doy, float elev_m)
{
    int npix = nrows * ncols;
    float wl[N_VNIR];
    enmap_vnir_wl(wl);

    /* Find band indices by wavelength proximity */
    int idx_540=-1, idx_600=-1, idx_680=-1,
        idx_865=-1, idx_940=-1, idx_1000=-1;
    for (int b = 0; b < N_VNIR; b++) {
        if (fabsf(wl[b]-0.540f) < 0.01f) idx_540  = b;
        if (fabsf(wl[b]-0.600f) < 0.01f) idx_600  = b;
        if (fabsf(wl[b]-0.680f) < 0.01f) idx_680  = b;
        if (fabsf(wl[b]-0.865f) < 0.01f) idx_865  = b;
        if (fabsf(wl[b]-0.940f) < 0.01f) idx_940  = b;
    }

    /* 1. Surface pressure */
    float pressure = retrieve_pressure_isa(elev_m);

    /* 2. O₃ from Chappuis */
    float o3_du = retrieve_o3_chappuis(
        toa + idx_540 * npix, toa + idx_600 * npix, toa + idx_680 * npix,
        npix, sza_deg, vza_deg);

    /* 3. H₂O from 940 nm triplet — pass EnMAP FWHM for narrowband K scaling */
    float *wvc = malloc(npix * sizeof(float));
    float *L_865  = toa + idx_865 * npix;
    float *L_940  = toa + idx_940 * npix;
    float *L_1000 = toa + (N_VNIR-1) * npix;      /* 1000 nm ≈ hi continuum */
    retrieve_h2o_940(L_865, L_940, L_1000,
                     /*fwhm_um=*/0.0065f,          /* EnMAP 6.5 nm FWHM */
                     npix, sza_deg, vza_deg, wvc);
    spatial_gaussian_filter(wvc, nrows, ncols, /*sigma_px=*/2.0f);
    float h2o_mean = 0.0f;
    for (int i = 0; i < npix; i++) h2o_mean += wvc[i];
    h2o_mean /= npix;

    /* 4. AOD from DDV — use band nearest to 470/660/860 nm */
    int idx_470=-1, idx_660=-1;
    float d470=1e9f, d660=1e9f;
    for (int b = 0; b < N_VNIR; b++) {
        if (fabsf(wl[b]-0.470f) < d470) { d470=fabsf(wl[b]-0.470f); idx_470=b; }
        if (fabsf(wl[b]-0.660f) < d660) { d660=fabsf(wl[b]-0.660f); idx_660=b; }
    }
    /* EnMAP has no 2130 nm in VNIR; proxy from NIR */
    float *swir_proxy = malloc(npix * sizeof(float));
    float *L_nir = toa + idx_865 * npix;
    for (int i = 0; i < npix; i++) swir_proxy[i] = L_nir[i] * 0.25f;

    float *aod_px = malloc(npix * sizeof(float));
    float aod_scene = retrieve_aod_ddv(
        toa + idx_470 * npix, toa + idx_660 * npix,
        L_nir, swir_proxy,
        npix, doy, sza_deg, aod_px);
    free(swir_proxy);
    retrieve_aod_maiac(aod_px, nrows, ncols, /*patch_sz=*/32);

    /* 5. Build full VNIR LUT (OpenMP-parallel, all 96 bands at once) */
    float aod_grid[] = { 0.0f, 0.1f, 0.2f, 0.4f, 0.8f };
    float h2o_grid[] = { 0.5f, 1.5f, 2.5f, 3.5f       };
    int N = 5 * 4 * N_VNIR;
    float *R_atm  = malloc(N * sizeof(float));
    float *T_down = malloc(N * sizeof(float));
    float *T_up   = malloc(N * sizeof(float));
    float *s_alb  = malloc(N * sizeof(float));

    LutConfig cfg = {
        .wl  = wl,       .n_wl  = N_VNIR,
        .aod = aod_grid, .n_aod = 5,
        .h2o = h2o_grid, .n_h2o = 4,
        .sza = sza_deg, .vza = vza_deg, .raa = raa_deg,
        .altitude_km      = 1000.0f,
        .atmo_model       = ATMO_US62,
        .aerosol_model    = AEROSOL_CONTINENTAL,
        .surface_pressure = pressure,
        .ozone_du         = o3_du,
    };
    LutArrays lut = { .R_atm  = R_atm,  .T_down = T_down,
                      .T_up   = T_up,   .s_alb  = s_alb  };
    atcorr_compute_lut(&cfg, &lut);   /* OpenMP: parallel over AOD × H₂O */

    /* 6. Quality mask */
    uint8_t *mask = malloc(npix);
    retrieve_quality_mask(toa + idx_470 * npix,
                          toa + idx_660 * npix,
                          toa + idx_865 * npix, NULL,
                          npix, doy, sza_deg, mask);

    /* 7. Per-pixel Lambertian inversion — vectorised over all 96 bands */
    float *Rs   = malloc(N_VNIR * sizeof(float));
    float *Tds  = malloc(N_VNIR * sizeof(float));
    float *Tus  = malloc(N_VNIR * sizeof(float));
    float *ss_b = malloc(N_VNIR * sizeof(float));

    #pragma omp parallel for schedule(static)
    for (int i = 0; i < npix; i++) {
        if (mask[i]) {
            for (int b = 0; b < N_VNIR; b++) boa[b*npix+i] = 0.0f;
            continue;
        }
        float Ra[N_VNIR], Td[N_VNIR], Tu[N_VNIR], sa[N_VNIR];
        for (int b = 0; b < N_VNIR; b++) {
            atcorr_lut_interp_pixel(&cfg, &lut, aod_px[i], wvc[i], wl[b],
                                    &Ra[b], &Td[b], &Tu[b], &sa[b]);
            boa[b*npix+i] = atcorr_invert(toa[b*npix+i],
                                           Ra[b], Td[b], Tu[b], sa[b]);
        }
    }

    /* 8. Adjacency correction + Tikhonov spectral smoothing per pixel */
    atcorr_lut_slice(&cfg, &lut, aod_scene, h2o_mean,
                     Rs, Tds, Tus, ss_b, NULL);
    for (int b = 0; b < N_VNIR; b++) {
        adjacency_correct_band(
            boa + b * npix, nrows, ncols,
            /*psf_radius_km=*/1.0f, /*pixel_size_m=*/30.0f,
            1.0f - Tds[b], ss_b[b], wl[b],
            aod_scene, pressure, sza_deg, vza_deg);
    }
    /* Reduce residual stripe noise across the spectrum (per pixel) */
    #pragma omp parallel for schedule(static)
    for (int i = 0; i < npix; i++) {
        float spec[N_VNIR];
        for (int b = 0; b < N_VNIR; b++) spec[b] = boa[b*npix+i];
        spectral_smooth_tikhonov(spec, N_VNIR, /*alpha=*/0.1f);
        for (int b = 0; b < N_VNIR; b++) boa[b*npix+i] = spec[b];
    }

    /* 9. DASF from NIR plateau (bands within 710–790 nm) */
    int n_dasf = 0;
    for (int b = 0; b < N_VNIR; b++)
        if (wl[b] >= 0.710f && wl[b] <= 0.790f) n_dasf++;
    float *wl_dasf   = malloc(n_dasf * sizeof(float));
    float *refl_dasf = malloc((long)n_dasf * npix * sizeof(float));
    int k = 0;
    for (int b = 0; b < N_VNIR; b++) {
        if (wl[b] >= 0.710f && wl[b] <= 0.790f) {
            wl_dasf[k] = wl[b];
            memcpy(refl_dasf + k*npix, boa + b*npix, npix * sizeof(float));
            k++;
        }
    }
    float *dasf_out = malloc(npix * sizeof(float));
    retrieve_dasf(refl_dasf, wl_dasf, n_dasf, npix, dasf_out);
    /* dasf_out[i] is now the Directional Area Scattering Factor per pixel */

    free(wvc); free(aod_px); free(mask);
    free(R_atm); free(T_down); free(T_up); free(s_alb);
    free(Rs); free(Tds); free(Tus); free(ss_b);
    free(wl_dasf); free(refl_dasf); free(dasf_out);
}
```

### Python

```python
import os, ctypes, math
import numpy as np

_here = os.path.dirname(os.path.abspath(__file__))
for _p in [os.environ.get("LIB_SIXSV", ""),
           os.path.join(_here, "..", "testsuite", "libsixsv.so")]:
    if _p and os.path.exists(_p):
        _lib = ctypes.CDLL(_p); break
else:
    raise ImportError("libsixsv.so not found")

_FP = ctypes.POINTER(ctypes.c_float)
def _fp(a): return np.ascontiguousarray(a, dtype=np.float32).ctypes.data_as(_FP)

class _Cfg(ctypes.Structure):
    _fields_ = [
        ("wl",_FP),("n_wl",ctypes.c_int),("aod",_FP),("n_aod",ctypes.c_int),
        ("h2o",_FP),("n_h2o",ctypes.c_int),
        ("sza",ctypes.c_float),("vza",ctypes.c_float),("raa",ctypes.c_float),
        ("altitude_km",ctypes.c_float),("atmo_model",ctypes.c_int),
        ("aerosol_model",ctypes.c_int),("surface_pressure",ctypes.c_float),
        ("ozone_du",ctypes.c_float),
        ("mie_r_mode",ctypes.c_float),("mie_sigma_g",ctypes.c_float),
        ("mie_m_real",ctypes.c_float),("mie_m_imag",ctypes.c_float),
        ("brdf_type",ctypes.c_int),("brdf_params",ctypes.c_float*5),
        ("enable_polar",ctypes.c_int),
    ]
class _Arr(ctypes.Structure):
    _fields_ = [("R_atm",_FP),("T_down",_FP),("T_up",_FP),("s_alb",_FP),
                ("T_down_dir",_FP),("R_atmQ",_FP),("R_atmU",_FP)]

def correct_enmap_vnir(toa, wl_um, nrows, ncols,
                        sza_deg, vza_deg, raa_deg,
                        doy, elev_m):
    """
    toa    : ndarray [n_bands, nrows*ncols] — TOA reflectance
    wl_um  : ndarray [n_bands]              — wavelengths in µm
    Returns boa : ndarray [n_bands, nrows*ncols],
            wvc : ndarray [nrows*ncols]    — H₂O column [g/cm²]
            dasf: ndarray [nrows*ncols]    — DASF per pixel
    """
    npix    = nrows * ncols
    n_bands = len(wl_um)
    wl_     = np.asarray(wl_um, dtype=np.float32)

    def nearest(target):
        return int(np.argmin(np.abs(wl_ - target)))

    # 1. Surface pressure
    _lib.retrieve_pressure_isa.argtypes = [ctypes.c_float]
    _lib.retrieve_pressure_isa.restype  = ctypes.c_float
    pressure = float(_lib.retrieve_pressure_isa(ctypes.c_float(elev_m)))

    # 2. O₃ from Chappuis
    _lib.retrieve_o3_chappuis.argtypes = [
        _FP, _FP, _FP, ctypes.c_int, ctypes.c_float, ctypes.c_float]
    _lib.retrieve_o3_chappuis.restype = ctypes.c_float
    o3_du = float(_lib.retrieve_o3_chappuis(
        _fp(toa[nearest(0.540)]), _fp(toa[nearest(0.600)]),
        _fp(toa[nearest(0.680)]),
        ctypes.c_int(npix),
        ctypes.c_float(sza_deg), ctypes.c_float(vza_deg)))

    # 3. H₂O from 940 nm triplet — fwhm_um=0.0065 activates narrowband K scaling
    _lib.retrieve_h2o_940.argtypes = [
        _FP, _FP, _FP, ctypes.c_float, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, _FP]
    _lib.retrieve_h2o_940.restype = None
    wvc = np.empty(npix, np.float32)
    _lib.retrieve_h2o_940(
        _fp(toa[nearest(0.865)]),
        _fp(toa[nearest(0.940)]),
        _fp(toa[nearest(1.000)]),
        ctypes.c_float(0.0065),        # EnMAP 6.5 nm FWHM
        ctypes.c_int(npix),
        ctypes.c_float(sza_deg), ctypes.c_float(vza_deg), _fp(wvc))

    _lib.spatial_gaussian_filter.argtypes = [
        _FP, ctypes.c_int, ctypes.c_int, ctypes.c_float]
    _lib.spatial_gaussian_filter.restype = None
    wvc_2d = np.ascontiguousarray(wvc.reshape(nrows, ncols))
    _lib.spatial_gaussian_filter(wvc_2d.ctypes.data_as(_FP),
                                  ctypes.c_int(nrows), ctypes.c_int(ncols),
                                  ctypes.c_float(2.0))
    wvc = wvc_2d.ravel()
    h2o_mean = float(wvc.mean())

    # 4. AOD — nearest EnMAP bands to 470/660/865 nm; proxy SWIR from NIR
    swir_proxy = (toa[nearest(0.865)] * 0.25).astype(np.float32)
    _lib.retrieve_aod_ddv.argtypes = [
        _FP, _FP, _FP, _FP, ctypes.c_int, ctypes.c_int, ctypes.c_float, _FP]
    _lib.retrieve_aod_ddv.restype = ctypes.c_float
    aod_px = np.empty(npix, np.float32)
    aod_scene = float(_lib.retrieve_aod_ddv(
        _fp(toa[nearest(0.470)]), _fp(toa[nearest(0.660)]),
        _fp(toa[nearest(0.865)]), _fp(swir_proxy),
        ctypes.c_int(npix), ctypes.c_int(doy),
        ctypes.c_float(sza_deg), _fp(aod_px)))

    _lib.retrieve_aod_maiac.argtypes = [
        _FP, ctypes.c_int, ctypes.c_int, ctypes.c_int]
    _lib.retrieve_aod_maiac.restype = None
    aod_2d = np.ascontiguousarray(aod_px.reshape(nrows, ncols))
    _lib.retrieve_aod_maiac(aod_2d.ctypes.data_as(_FP),
                             ctypes.c_int(nrows), ctypes.c_int(ncols),
                             ctypes.c_int(32))

    # 5. Build full VNIR LUT (all n_bands wavelengths at once)
    aod_ = np.array([0.0, 0.1, 0.2, 0.4, 0.8], dtype=np.float32)
    h2o_ = np.array([0.5, 1.5, 2.5, 3.5],       dtype=np.float32)
    N = n_bands * aod_.size * h2o_.size
    Ra, Td, Tu, ss = [np.empty(N, np.float32) for _ in range(4)]

    cfg_c = _Cfg(wl=_fp(wl_), n_wl=n_bands,
                 aod=_fp(aod_), n_aod=aod_.size,
                 h2o=_fp(h2o_), n_h2o=h2o_.size,
                 sza=sza_deg, vza=vza_deg, raa=raa_deg,
                 altitude_km=1000., atmo_model=1, aerosol_model=1,
                 surface_pressure=pressure, ozone_du=o3_du)
    arr_c = _Arr(R_atm=_fp(Ra), T_down=_fp(Td),
                 T_up=_fp(Tu),  s_alb=_fp(ss))
    _lib.atcorr_compute_lut(ctypes.byref(cfg_c), ctypes.byref(arr_c))

    lut = dict(cfg_c=cfg_c, arr_c=arr_c,
               wl=wl_, aod=aod_, h2o=h2o_,
               _Ra=Ra, _Td=Td, _Tu=Tu, _ss=ss)

    # 6. Quality mask
    mask = np.zeros(npix, dtype=np.uint8)
    _lib.retrieve_quality_mask.argtypes = [
        _FP, _FP, _FP, _FP, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.POINTER(ctypes.c_uint8)]
    _lib.retrieve_quality_mask.restype = None
    _lib.retrieve_quality_mask(
        _fp(toa[nearest(0.470)]), _fp(toa[nearest(0.660)]),
        _fp(toa[nearest(0.865)]), None,
        ctypes.c_int(npix), ctypes.c_int(doy), ctypes.c_float(sza_deg),
        mask.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8)))

    # 7. Per-band Lambertian inversion using scene-mean AOD and per-pixel H₂O
    _lib.atcorr_lut_slice.argtypes = [
        ctypes.POINTER(_Cfg), ctypes.POINTER(_Arr),
        ctypes.c_float, ctypes.c_float,
        _FP, _FP, _FP, _FP, _FP]
    _lib.atcorr_lut_slice.restype = None

    Rs  = np.empty(n_bands, np.float32)
    Tds = np.empty(n_bands, np.float32)
    Tus = np.empty(n_bands, np.float32)
    sas = np.empty(n_bands, np.float32)
    _lib.atcorr_lut_slice(ctypes.byref(cfg_c), ctypes.byref(arr_c),
                          ctypes.c_float(aod_scene), ctypes.c_float(h2o_mean),
                          _fp(Rs), _fp(Tds), _fp(Tus), _fp(sas), None)

    boa = np.where(
        mask[np.newaxis, :] == 0,
        np.clip(
            (toa - Rs[:, np.newaxis])
            / (Tds[:, np.newaxis] * Tus[:, np.newaxis] + 1e-10),
            -0.1, 2.0),
        0.0).astype(np.float32)
    boa /= (1.0 + sas[:, np.newaxis] * boa + 1e-10)

    # 8. Adjacency correction — 1 km PSF at 30 m GSD
    _lib.adjacency_correct_band.argtypes = [
        _FP, ctypes.c_int, ctypes.c_int,
        ctypes.c_float, ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float, ctypes.c_float,
        ctypes.c_float, ctypes.c_float]
    _lib.adjacency_correct_band.restype = None
    for b in range(n_bands):
        band_2d = np.ascontiguousarray(boa[b].reshape(nrows, ncols))
        _lib.adjacency_correct_band(
            band_2d.ctypes.data_as(_FP),
            ctypes.c_int(nrows), ctypes.c_int(ncols),
            ctypes.c_float(1.0), ctypes.c_float(30.0),
            ctypes.c_float(float(1.0 - Tds[b])), ctypes.c_float(float(sas[b])),
            ctypes.c_float(float(wl_[b])),
            ctypes.c_float(aod_scene), ctypes.c_float(pressure),
            ctypes.c_float(sza_deg), ctypes.c_float(vza_deg))
        boa[b] = band_2d.ravel()

    # 9. Tikhonov spectral smoothing to reduce residual stripe noise
    _lib.spectral_smooth_tikhonov.argtypes = [_FP, ctypes.c_int, ctypes.c_float]
    _lib.spectral_smooth_tikhonov.restype  = None
    for i in range(npix):
        spec = np.ascontiguousarray(boa[:, i])
        _lib.spectral_smooth_tikhonov(_fp(spec), ctypes.c_int(n_bands),
                                       ctypes.c_float(0.1))
        boa[:, i] = spec

    # 10. DASF from NIR plateau bands (710–790 nm)
    dasf_mask  = (wl_ >= 0.710) & (wl_ <= 0.790)
    wl_dasf    = wl_[dasf_mask]
    refl_dasf  = np.ascontiguousarray(boa[dasf_mask])   # [n_dasf, npix]
    _lib.retrieve_dasf.argtypes = [_FP, _FP, ctypes.c_int, ctypes.c_int, _FP]
    _lib.retrieve_dasf.restype  = None
    dasf_out   = np.empty(npix, np.float32)
    _lib.retrieve_dasf(_fp(refl_dasf.ravel()), _fp(wl_dasf),
                        ctypes.c_int(wl_dasf.size), ctypes.c_int(npix),
                        _fp(dasf_out))

    return boa, wvc, dasf_out
```

---

## Custom Mie aerosol

#### C

```c
LutConfig cfg = {
    /* ... */
    .aerosol_model = AEROSOL_CUSTOM,
    .mie_r_mode    = 0.12f,   /* log-normal mode radius [µm] */
    .mie_sigma_g   = 1.80f,   /* geometric standard deviation */
    .mie_m_real    = 1.50f,   /* real refractive index @ 550 nm */
    .mie_m_imag    = 0.008f,  /* imaginary refractive index @ 550 nm */
};
```

#### Python

```python
cfg = ac.LutConfig(
    # ...
    aerosol_model=9,       # AEROSOL_CUSTOM
    mie_r_mode=0.12,
    mie_sigma_g=1.80,
    mie_m_real=1.50,
    mie_m_imag=0.008,
)
```

## SRF gas-transmittance correction (requires libRadtran)

#### C

```c
SrfConfig srf_cfg = {
    .fwhm_um      = fwhm_array,   /* per-band FWHM [µm], NULL = all bands */
    .threshold_um = 0.005f,       /* only correct bands with FWHM < 5 nm */
};
SrfCorrection *srf = atcorr_srf_compute(&srf_cfg, &cfg);
if (srf) {
    atcorr_compute_lut(&cfg, &lut);
    atcorr_srf_apply(srf, &cfg, &lut);   /* modifies T_down, T_up in-place */
    atcorr_srf_free(srf);
}
```

#### Python

```python
lut = ac.compute_lut(cfg)
# apply_srf_correction() calls srf_compute + srf_apply + srf_free internally
ac.apply_srf_correction(cfg, lut,
                         fwhm_um=fwhm_array,
                         threshold_nm=5.0)  # only narrow bands < 5 nm FWHM
```

## Thread control

#### C

```c
/* OMP_NUM_THREADS controls all parallelism — no API call needed */
```

```sh
export OMP_NUM_THREADS=8   # use 8 cores
./your_program
```

#### Python

```python
import atcorr as ac
ac.omp_set_num_threads(8)   # or: os.environ["OMP_NUM_THREADS"] = "8"
```
