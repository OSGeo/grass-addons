<!-- markdownlint-disable -->
# libsixsv — 6SV2.1 Atmospheric Correction Library

> **GitHub**: <https://github.com/yannchemin/libsixsv>

A C11 port of the **6SV2.1** (Second Simulation of the Satellite Signal in the Solar
Spectrum) radiative transfer model, designed for operational atmospheric correction of
hyperspectral remote sensing imagery.  The library backs the
[i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr) GRASS GIS module but
can also be used as a standalone shared library.

## Port scope and reference

The numerical reference used for compatibility testing is
[`NakamuraTakashi/6SV2.1`](https://github.com/NakamuraTakashi/6SV2.1) at commit
`7deb2289cfe23c9b1d1b48d7647f76604ef75fa4`. The original Fortran program is
the authority for routines described as direct ports. Operational features that do not
exist in that program are identified as C extensions rather than 6SV2.1 ports.

| Functionality | C implementation | Status |
|---|---|---|
| US62 and standard atmosphere profiles | `atmosphere.c`, `pressure.c` | Direct data/routine port; basic subroutines tested against Fortran |
| Rayleigh optical depth, Chandrasekhar reflectance, spherical albedo | `rayleigh.c`, `chand.c`, `csalbr.c` | Direct ports; tested against Fortran |
| Solar irradiance and Earth-Sun distance | `solar.c`, `solar_table.c` | Table port with C interpolation; tested against Fortran |
| Standard continental, maritime, and urban aerosol components | `aerosol_tables.c`, `aerosol.c` | Direct component-table and mixture port; corrected and pipeline-tested against Fortran |
| Scalar scattering solver | `discom.c`, `rt.c`, `scatra.c`, `kernel.c`, `interp.c` | Directly derived from Fortran; satellite continental pipeline tested within 0.85% per coefficient |
| Gas absorption | `gas_abs.c`, `gas_tables.c` | Direct ABSTRA-derived calculation with separate C path API; tables regenerated from all 256 Fortran intervals and tested in the pipeline |
| Stokes-I vector result | `ospol.c`, `kernelpol.c` | Rewritten vector solver; satellite Stokes-I pipeline tested within 0.85% |
| Aerosol Stokes Q/U | `trunca.c`, `kernelpol.c` | **Known gap:** aerosol Q/U phase matrices and full polarized TRUNCA coefficients are not yet ported; Q/U output is Rayleigh-dominated and is not 6SV2.1-compatible |
| Satellite sensor path | `lut.c`, `discom.c` | Corrected to the Fortran `idatmp=4`, full target-to-sensor aerosol/Rayleigh column convention |
| Aircraft sensor path | `lut.c` | **Known gap:** partial atmospheric and aerosol columns are approximated; `PRESPLANE` semantics are not fully ported |
| `AEROSOL_DESERT` | public API and `aerosol.c` | **Known gap:** currently falls through to the continental mixture; BDM tables are not ported |
| Custom Mie aerosol | `mie.c` | C extension, not equivalent to a complete original 6SV user-defined aerosol workflow |
| AOD x H2O x wavelength LUT | `lut.c`, `correct.c` | C extension built from the ported coefficients |
| Lambertian inversion | `atcorr.c`, `correct.c` | C implementation of the 6SV coefficient equation |
| BRDF, terrain, adjacency, retrieval, OE, uncertainty, spatial filtering | corresponding C modules | Operational C extensions; not direct Fortran 6SV2.1 ports |
| OpenMP and GPU directives | LUT and image-level modules | C extension |

Do not interpret a passing scalar or Stokes-I pipeline test as validation of aerosol
Stokes Q/U, aircraft paths, the desert model, every atmosphere/aerosol combination, or
the operational retrieval extensions. Each of those requires its own pinned reference
matrix.

## Numerical workflows

### Original 6SV2.1 reference workflow

For each monochromatic validation wavelength, the original executable performs:

```text
input geometry/atmosphere/aerosol/surface
  -> atmosphere profile and target/sensor columns
  -> AEROSO standard aerosol mixture
  -> DISCOM at the 20 internal wavelengths
  -> INTERP at the requested wavelength
  -> ABSTRA gas transmittance
  -> surface-atmosphere coupling
  -> apparent reflectance and radiance
```

The committed pipeline fixture uses SZA 30 degrees, VZA 0 degrees, relative azimuth
0 degrees, US62, continental aerosol, AOD 0.2, H2O 2.0 g/cm2, ozone 300 DU,
satellite altitude, Lambertian surface reflectance 0.20, and wavelengths 450, 550,
650, and 850 nm.

### libsixsv LUT workflow

`atcorr_compute_lut()` performs the following for each AOD node:

```text
LutConfig
  -> sixs_init_atmosphere()
  -> optional pressure adjustment
  -> sixs_aerosol_init()
  -> sixs_discom() at 20 internal wavelengths
       -> ODRAYL optical depth
       -> TRUNCA phase expansion
       -> OS or OSPOL atmospheric path reflectance
       -> SCATRA direct/diffuse transmission and spherical albedo
  -> sixs_interp() at every LUT wavelength
  -> sixs_gas_transmittance() for every H2O/wavelength node
  -> combine scattering and gas transmission
  -> LutArrays: R_atm, T_down, T_up, s_alb
```

The original program computes gas and scattering in one driver. The C LUT deliberately
computes them separately and combines them as:

```text
T_down = T_down_scattering * T_down_gas
T_up   = T_up_scattering   * T_up_gas
```

For a satellite, `taer55p`, `trayp`, and the gas column represent the full column
between the target and sensor, matching the original `idatmp=4` convention.

### Standard aerosol workflow

For continental, maritime, and urban aerosols, the C path now follows `AEROSO.f`:

```text
load DUST/WATE/OCEA/SOOT extinction, scattering, asymmetry, and phase tables
  -> load exact component vi integrals from the four Fortran component routines
  -> cij = (ci / vi) / sum(ci / vi)
  -> normalize extinction at 550 nm
  -> scattering-weight component phase functions
  -> pass optical properties and phase expansion to DISCOM
```

The exact original mixtures are continental `(0.70, 0.29, 0.00, 0.01)`, maritime
`(0.00, 0.05, 0.95, 0.00)`, and urban `(0.17, 0.61, 0.00, 0.22)` in
`(dust, water-soluble, oceanic, soot)` order.

### Gas workflow

The gas path follows the relevant `ABSTRA.f` operations:

```text
wavelength -> wavenumber and one of six 256-interval tables
  -> gas-specific Curtis-Godson coefficients
  -> trapezoidal pressure/profile column integration
  -> H2O/CO2/O2/N2O/CH4/CO transmittance
  -> independent visible ozone continuum transmittance
  -> product of gas-species transmittances for each direction
```

The ACR tables are generated by `tools/extract_gas_tables.py`. Regeneration is part of
the reproducible workflow because a previous generated table omitted the first eight
intervals of every Fortran gas table.

### Surface-reflectance inversion

For Lambertian correction, let `rho_toa` be apparent TOA reflectance and let the LUT
provide atmospheric path reflectance `R_atm`, total directional transmittances, and
spherical albedo `s_alb`:

```text
y       = (rho_toa - R_atm) / (T_down * T_up)
rho_boa = y / (1 + s_alb * y)
```

Radiance is converted to `rho_toa` with band solar irradiance, solar zenith, and
Earth-Sun distance before this inversion.

## Corrected compatibility defects

The pinned pipeline comparison identified and corrected these defects:

1. Replaced incorrect aerosol `vi` normalizers with values from
   `DUST.f`, `WATE.f`, `OCEA.f`, and `SOOT.f`.
2. Restored the original maritime and urban mixture ratios and shared one mixture table
   between aerosol initialization and DISCOM phase mixing.
3. Restored satellite `idatmp=4`, `ftray=1`, and full target-to-sensor optical depths.
4. Restored the separate solar and view angular endpoints used by `SCATRA.f` for
   downward and upward ISO calculations.
5. Restored visible ozone absorption outside the six near-infrared gas tables.
6. Restored trapezoidal atmospheric-column integration from `ABSTRA.f`.
7. Regenerated all gas ACR arrays without dropping the first eight intervals.
8. Restored the ABSTRA CO2/O2 spectral cutoffs, 3.3-4.0 um ozone table, and H2O
   continuum path.

## Pipeline parity results

The following values come from the committed fixture and were independently regenerated
with the pinned Fortran executable. "Before" is the library state before the corrections
above; "after" is the corrected vector/Stokes-I LUT path.

| nm | Coefficient | Fortran | Before | After | Before error | After error |
|---:|---|---:|---:|---:|---:|---:|
| 450 | R_atm | 0.099720 | 0.086073 | 0.098950 | -13.685% | -0.772% |
| 450 | T_down | 0.829247 | 0.804746 | 0.828223 | -2.955% | -0.123% |
| 450 | T_up | 0.852081 | 0.804746 | 0.847418 | -5.555% | -0.547% |
| 450 | s_alb | 0.190940 | 0.137760 | 0.189396 | -27.852% | -0.809% |
| 550 | R_atm | 0.049500 | 0.041287 | 0.049102 | -16.592% | -0.804% |
| 550 | T_down | 0.871633 | 0.864959 | 0.871116 | -0.766% | -0.059% |
| 550 | T_up | 0.890346 | 0.864959 | 0.886229 | -2.851% | -0.462% |
| 550 | s_alb | 0.120280 | 0.080970 | 0.119327 | -32.682% | -0.793% |
| 650 | R_atm | 0.028770 | 0.024139 | 0.028528 | -16.098% | -0.842% |
| 650 | T_down | 0.900106 | 0.860398 | 0.899881 | -4.412% | -0.025% |
| 650 | T_up | 0.915278 | 0.864702 | 0.911738 | -5.526% | -0.387% |
| 650 | s_alb | 0.084630 | 0.057256 | 0.083957 | -32.346% | -0.795% |
| 850 | R_atm | 0.013180 | 0.013522 | 0.013075 | +2.596% | -0.799% |
| 850 | T_down | 0.950123 | 0.913028 | 0.950173 | -3.904% | +0.005% |
| 850 | T_up | 0.958590 | 0.913880 | 0.955968 | -4.664% | -0.274% |
| 850 | s_alb | 0.050300 | 0.042857 | 0.049883 | -14.798% | -0.829% |

The end-to-end test passes the original Fortran radiance through `i.hyper.atcorr`; the
known input surface reflectance is 0.20:

| Wavelength | Before | After | Before error | After error |
|---:|---:|---:|---:|---:|
| 450 nm | 0.239458382 | 0.202101156 | +19.729% | +1.051% |
| 550 nm | 0.216213956 | 0.198335990 | +8.107% | -0.832% |
| 650 nm | 0.227028787 | 0.199821517 | +13.514% | -0.089% |
| 850 nm | 0.218052611 | 0.200656921 | +9.026% | +0.328% |

The per-nanometre and per-micrometre GRASS inputs agree within `1.5e-8` after correction.
The remaining sub-percent coefficient residuals are retained and tested; they are not
removed with empirical calibration factors.

## Features

- **Radiative transfer solver**: DISCOM discrete-ordinate method (up to 20 scattering
  orders), with validated scalar and vector Stokes-I output; aerosol Stokes Q/U remains
  a documented compatibility gap
- **3-D look-up table** computation over [AOD × H₂O × wavelength]
- **Per-pixel atmospheric correction** — Lambertian and BRDF-coupled inversion
- **Scene-based automatic retrievals**
  - Water vapour (H₂O) from 940 nm band depth or triplet
  - Aerosol optical depth (AOD) via MODIS dark-dense-vegetation (DDV) and spatial
    regularisation (MAIAC-inspired)
  - Ozone from Chappuis 600 nm band
  - Surface pressure from O₂-A 760 nm or ISA elevation
- **Joint AOD + H₂O optimal estimation** (MAP grid-search + refinement)
- **BRDF surface models**: Lambertian, Rahman, Roujean, Hapke, ocean, and five
  Ross-Li variants; NBAR normalisation; MCD43 BRDF disaggregation
- **Topographic correction** — illumination angle and transmittance
- **Adjacency effect correction** (Vermote 1997)
- **Uncertainty propagation** — instrument noise and AOD perturbation
- **SRF convolution** for fine-resolution gas transmittance (requires libRadtran)
- **OpenMP parallelisation** — see below

## Parallelism with OpenMP

Atmospheric correction of hyperspectral scenes is compute-intensive: a single
LUT spans hundreds of radiative-transfer calls across an [AOD × H₂O × wavelength]
grid, and per-pixel inversion and retrieval must then run over millions of pixels.
libsixsv uses **OpenMP** throughout to exploit all available CPU cores with no
changes required in the calling code.

Parallelised workloads:

| Workload | Parallelisation strategy |
|---|---|
| LUT grid computation (`atcorr_compute_lut`) | Each AOD node runs in a separate thread; the 6SV context (`sixs_ctx`) is per-thread to avoid data races |
| Per-pixel correction (`atcorr_invert`, `atcorr_invert_brdf`) | Pixel loop distributed across threads |
| Joint AOD + H₂O retrieval (`oe_invert_aod_h2o`) | Grid-search over candidate (AOD, H₂O) pairs parallelised |
| Spatial filtering (`spatial.h`) | Collapsed 2-D pixel loop over both passes |
| Uncertainty propagation (`uncertainty_compute_band`) | Per-pixel loop distributed across threads |

The thread count is controlled at runtime via the standard OpenMP environment
variable — no recompilation needed:

```sh
export OMP_NUM_THREADS=16   # use 16 cores
```

On a modern multi-core workstation, LUT construction and full-scene correction
scale near-linearly with core count.

### GPU offload via OpenMP target

The pixel-level workloads — uncertainty propagation and spatial filtering
(Gaussian and box) — are annotated with **OpenMP target** directives
(`target teams distribute parallel for`) and offload transparently to a GPU
when one is available.  The radiative-transfer solver itself remains on the CPU
(its successive-orders loop is inherently sequential).

GPU offload behaviour by workload:

| Workload | Directive | Notes |
|---|---|---|
| Uncertainty propagation | `target teams distribute parallel for` | `refl_band` mapped `to:`, `sigma_out` mapped `from:` |
| Spatial box filter | `target data` + two `target teams distribute parallel for collapse(2)` | Intermediate buffer `tmp` kept on device between passes (`map(alloc:)`) |
| Spatial Gaussian filter | Same as box filter | Kernel array mapped `to:`; `data` mapped `tofrom:` (in-place) |

When no GPU device is present, or when compiled without offload support, all
directives fall back silently to host execution — no code changes or
recompilation are needed to switch between CPU and GPU paths.

To enable GPU offload, pass `OFFLOAD_FLAGS` at build time (see `INSTALL.md`).

## Aerosol and atmosphere models

| Identifier            | Description                  |
|-----------------------|------------------------------|
| `AEROSOL_NONE`        | Rayleigh scattering only      |
| `AEROSOL_CONTINENTAL` | Continental mixture           |
| `AEROSOL_MARITIME`    | Maritime mixture              |
| `AEROSOL_URBAN`       | Urban mixture                 |
| `AEROSOL_DESERT`      | Desert dust                   |
| `AEROSOL_CUSTOM`      | Custom Mie log-normal         |

| Identifier    | Description                 |
|---------------|-----------------------------|
| `ATMO_US62`   | US Standard Atmosphere 1962 |
| `ATMO_MIDSUM`    | Mid-latitude summer      |
| `ATMO_MIDWIN`    | Mid-latitude winter      |
| `ATMO_TROPICAL`  | Tropical                 |
| `ATMO_SUBSUM`    | Sub-arctic summer        |
| `ATMO_SUBWIN`    | Sub-arctic winter        |

## Public API

The public headers are installed to `include/grass/` inside GRASS (or to a
prefix of your choice in standalone mode):

| Header              | Purpose                                      |
|---------------------|----------------------------------------------|
| `atcorr.h`          | LUT computation and per-pixel inversion       |
| `brdf.h`          | BRDF model evaluation and NBAR normalisation  |
| `retrieve.h`      | Scene-based retrieval algorithms              |
| `oe_invert.h`     | Joint AOD + H₂O optimal estimation           |
| `adjacency.h`     | Adjacency effect correction                  |
| `terrain.h`       | Topographic corrections                      |
| `uncertainty.h`   | Noise and AOD uncertainty propagation        |
| `spatial.h`       | Gaussian and box filtering (NaN-safe)        |
| `surface_model.h` | 3-component surface prior (VEG/SOIL/WATER)   |
| `spectral_brdf.h` | MCD43 BRDF disaggregation + Tikhonov smoothing |

## Installing the Debian package

Build and install the packages with:

```sh
make deb                          # runs dpkg-buildpackage -us -uc -b
sudo dpkg -i ../libsixsv1_*.deb ../libsixsv-dev_*.deb
```

After installation:

- Headers: `/usr/include/sixsv/` (`atcorr.h`, `brdf.h`, `retrieve.h`, …)
- Library: `/usr/lib/x86_64-linux-gnu/libsixsv.so.1` (registered with ldconfig)
- Development symlink: `/usr/lib/x86_64-linux-gnu/libsixsv.so`

For the **Debian standalone build** of
[i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr), also install
[libras3d-dev](https://github.com/yannchemin/libras3d) — the GRASS API
replacement that routes cube I/O through libtiff/libgeotiff and libhdf5.

## Compiling against the installed library

Place `-lsixsv -lm -fopenmp` **after** the source file on the command line
(GCC resolves symbols left-to-right; putting libraries before the object
file causes undefined-reference errors):

```sh
gcc -std=c11 -O2 -I/usr/include/sixsv \
    my_program.c \
    -lsixsv -lm -fopenmp \
    -o my_program
```

## Python (ctypes)

The examples in `examples/` load the library directly — no wrapper package
needed:

```python
import ctypes, ctypes.util
lib = ctypes.CDLL(ctypes.util.find_library("sixsv") or "libsixsv.so.1")
```

## Testsuite

The `testsuite/` directory contains a self-contained test suite that validates
numerical correctness, OpenMP parallelism, and GPU offload behaviour.

| File                         | What it tests |
|------------------------------|---------------|
| `Makefile`                   | Builds `libsixsv.so` (standalone) and the Fortran driver; exposes `make test`, `make test-fortran`, `make test-openmp` |
| `_support.py` | ctypes bindings for all library functions and OpenMP runtime helpers (not a test file) |
| `test_6sv_compat.f90` | Fortran driver that calls 6SV2.1 subroutines (CHAND, ODRAYL, VARSOL, SOLIRR, CSALBR, GAUSS) and prints `key=value` reference values |
| `test_fortran_compat.py` | 25 tests comparing 6SV2.1 Fortran subroutines against the C port (rtol 1e-5 to 5e-3 depending on precision convention) |
| `test_6sv21_pipeline_parity.py` | Pinned satellite/continental coefficient and Fortran-to-C inversion parity at 450, 550, 650, and 850 nm |
| `data/6sv21_satellite_continental.json` | Pinned Fortran coefficients, radiances, and pre-correction results |
| `generate_6sv21_reference.py` | Runs the original `sixsV2.1` executable and checks that it regenerates the committed fixture |
| `test_lut.py` | 30+ tests: LUT shape, physical bounds, monotonicity with AOD, aerosol model differences, bilinear interpolation, per-pixel inversion, polarization (Q/U) |
| `test_solar.py` | 12 tests: solar irradiance spectrum (E0 vs Thuillier reference ±15 %) and Earth–Sun distance (perihelion, aphelion, eccentricity) |
| `test_openmp.py` | 25+ tests: OpenMP runtime availability, LUT serial-vs-parallel consistency (rtol 1e-5), spatial filter correctness and NaN handling, GPU-path reproducibility on 512 × 512 arrays |

```sh
cd testsuite

make lib              # build libsixsv.so
make test             # build the Fortran driver and run all tests
make test-fortran     # Fortran compat + LUT + solar only
make test-openmp      # OpenMP / GPU tests only

# or run pytest directly after building:
LIB_SIXSV=./libsixsv.so python3 -m pytest -v
```

## Manual compatibility test procedure

### 1. Build the pinned original Fortran executable

```sh
git clone https://github.com/NakamuraTakashi/6SV2.1.git /tmp/6SV2.1
git -C /tmp/6SV2.1 checkout 7deb2289cfe23c9b1d1b48d7647f76604ef75fa4
make -C /tmp/6SV2.1/src clean
make -C /tmp/6SV2.1/src sixs \
    EXTRA="-O -ffixed-line-length-132 -fallow-argument-mismatch -std=legacy"
export SIXSV2=/tmp/6SV2.1/src
```

The executable is `$SIXSV2/sixsV2.1`. Keep this source tree and executable if repeated
Fortran comparisons are required.

### 2. Regenerate and verify the gas tables

```sh
cd src/imagery/i.hyper/i.hyper.atcorr/libsixsv
python3 tools/extract_gas_tables.py "$SIXSV2"
clang-format -i src/gas_tables.c
git diff --exit-code -- src/gas_tables.c
```

No diff means the committed C arrays exactly reflect the pinned Fortran ACR tables.

### 3. Build and run all library tests

```sh
cd testsuite
make clean
make lib
make fortran SIXSV2="$SIXSV2"
SIXSV2="$SIXSV2" LIB_SIXSV="$PWD/libsixsv.so" \
    python3 -m pytest -v
```

The complete suite currently contains 103 tests: 25 direct Fortran-subroutine tests,
two full pipeline parity tests, and 76 LUT, inversion, solar, OpenMP, filtering, and
extension tests.

### 4. Rerun the original executable pipeline cases

```sh
./generate_6sv21_reference.py "$SIXSV2/sixsV2.1" --check
```

This runs all four original Fortran simulations, prints the coefficient table, and
fails if it differs from `data/6sv21_satellite_continental.json`.

### 5. Rerun the persistent GRASS end-to-end test

The validation maps are in project `ihajper`, mapset `PERMANENT`, under GIS database
`/media/tomazz/Data1/grass-data`. They intentionally remain available:

```text
atcorr_validation_radiance_um
atcorr_validation_radiance_nm
atcorr_validation_reflectance_um                 # before correction
atcorr_validation_reflectance_corrected_um       # after correction
atcorr_validation_reflectance_corrected_nm
atcorr_validation_corrected_error
atcorr_validation_corrected_unit_delta
```

Inside that GRASS session, run:

```sh
g.region raster_3d=atcorr_validation_radiance_um

i.hyper.atcorr -P --overwrite \
    input=atcorr_validation_radiance_um \
    output=atcorr_validation_reflectance_corrected_um \
    lut=/tmp/atcorr_validation_corrected_um.lut \
    sza=30 vza=0 raa=0 altitude=1000 \
    atmosphere=us62 aerosol=continental ozone=300 \
    aod=0.2,0.3 aod_val=0.2 h2o=2.0,3.0 h2o_val=2.0 \
    wl_min=450 wl_max=850 wl_step=100 doy=183

r3.out.ascii -h input=atcorr_validation_reflectance_corrected_um precision=12
r3.out.ascii -h input=atcorr_validation_corrected_unit_delta precision=12
g.region region=atcorr_validation_original_region
```

Expected corrected reflectances are `0.202101156`, `0.198335990`, `0.199821517`,
and `0.200656921`. Always restore `atcorr_validation_original_region`; do not remove
the validation maps.

## Dependencies

## Runtime

- C standard library (`libm`)
- OpenMP (parallelisation)
- libRadtran `uvspec` binary — *optional*, required only for `atcorr_srf_compute()`

## Build

- C11-capable compiler (GCC ≥ 5 or Clang ≥ 6)
- GRASS GIS development environment (GRASS build) **or** GNU Make + standard
  POSIX tools (standalone build)

## Related repositories

| Repository                                                          | Relationship           | Description |
|---------------------------------------------------------------------|------------------------|-------------|
| [i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr)       | **Downstream consumer** | GRASS GIS module that links libsixsv for 6SV2.1 atmospheric correction of hyperspectral cubes |
| [libras3d](https://github.com/yannchemin/libras3d) | **Peer — Debian standalone** | Drop-in GRASS raster3d API replacement; used alongside libsixsv when building i.hyper.atcorr without GRASS (`DEBIAN_BUILD=1`) |

## License

This is free and unencumbered software released into the public domain.  
See <https://unlicense.org> for the full text.
