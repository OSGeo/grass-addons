# libsixsv — 6SV2.1 Atmospheric Correction Library

> **GitHub**: <https://github.com/yannchemin/libsixsv>

A C11 port of the **6SV2.1** (Second Simulation of the Satellite Signal in the Solar
Spectrum) radiative transfer model, designed for operational atmospheric correction of
hyperspectral remote sensing imagery.  The library backs the
[i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr) GRASS GIS module but
can also be used as a standalone shared library.

## Features

- **Radiative transfer solver**: DISCOM discrete-ordinate method (up to 20 scattering
  orders), with optional vector (Stokes I/Q/U) polarization via successive-orders
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
lib6sv uses **OpenMP** throughout to exploit all available CPU cores with no
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

| Identifier       | Description              |
|------------------|--------------------------|
| `ATMO_US62`      | US Standard Atmosphere 1962 |
| `ATMO_MIDSUM`    | Mid-latitude summer      |
| `ATMO_MIDWIN`    | Mid-latitude winter      |
| `ATMO_TROPICAL`  | Tropical                 |
| `ATMO_SUBSUM`    | Sub-arctic summer        |
| `ATMO_SUBWIN`    | Sub-arctic winter        |

## Public API

The public headers are installed to `include/grass/` inside GRASS (or to a
prefix of your choice in standalone mode):

| Header            | Purpose                                      |
|-------------------|----------------------------------------------|
| `atcorr.h`        | LUT computation and per-pixel inversion       |
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

**Compiling against the installed library**

Place `-lsixsv -lm -fopenmp` **after** the source file on the command line
(GCC resolves symbols left-to-right; putting libraries before the object
file causes undefined-reference errors):

```sh
gcc -std=c11 -O2 -I/usr/include/sixsv \
    my_program.c \
    -lsixsv -lm -fopenmp \
    -o my_program
```

**Python (ctypes)**

The examples in `examples/` load the library directly — no wrapper package
needed:

```python
import ctypes, ctypes.util
lib = ctypes.CDLL(ctypes.util.find_library("sixsv") or "libsixsv.so.1")
```

## Testsuite

The `testsuite/` directory contains a self-contained test suite that validates
numerical correctness, OpenMP parallelism, and GPU offload behaviour.

| File | What it tests |
|---|---|
| `Makefile` | Builds `libsixsv.so` (standalone) and the Fortran driver; exposes `make test`, `make test-fortran`, `make test-openmp` |
| `_support.py` | ctypes bindings for all library functions and OpenMP runtime helpers (not a test file) |
| `test_6sv_compat.f90` | Fortran driver that calls 6SV2.1 subroutines (CHAND, ODRAYL, VARSOL, SOLIRR, CSALBR, GAUSS) and prints `key=value` reference values |
| `test_fortran_compat.py` | 35 tests comparing 6SV2.1 Fortran subroutines against the C port (rtol 1e-5 – 5e-3 depending on precision convention) |
| `test_lut.py` | 30+ tests: LUT shape, physical bounds, monotonicity with AOD, aerosol model differences, bilinear interpolation, per-pixel inversion, polarization (Q/U) |
| `test_solar.py` | 12 tests: solar irradiance spectrum (E0 vs Thuillier reference ±15 %) and Earth–Sun distance (perihelion, aphelion, eccentricity) |
| `test_openmp.py` | 25+ tests: OpenMP runtime availability, LUT serial-vs-parallel consistency (rtol 1e-5), spatial filter correctness and NaN handling, GPU-path reproducibility on 512 × 512 arrays |

```sh
cd testsuite

make                  # build libsixsv.so and the Fortran driver
make test             # run all tests
make test-fortran     # Fortran compat + LUT + solar only
make test-openmp      # OpenMP / GPU tests only

# or run pytest directly after building:
LIB_SIXSV=./libsixsv.so python3 -m pytest -v
```

## Dependencies

**Runtime**

- C standard library (`libm`)
- OpenMP (parallelisation)
- libRadtran `uvspec` binary — *optional*, required only for `atcorr_srf_compute()`

**Build**

- C11-capable compiler (GCC ≥ 5 or Clang ≥ 6)
- GRASS GIS development environment (GRASS build) **or** GNU Make + standard
  POSIX tools (standalone build)

## Related repositories

| Repository | Relationship | Description |
|---|---|---|
| [i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr) | **Downstream consumer** | GRASS GIS module that links libsixsv for 6SV2.1 atmospheric correction of hyperspectral cubes |
| [libras3d](https://github.com/yannchemin/libras3d) | **Peer — Debian standalone** | Drop-in GRASS raster3d API replacement; used alongside libsixsv when building i.hyper.atcorr without GRASS (`DEBIAN_BUILD=1`) |

## License

This is free and unencumbered software released into the public domain.  
See <https://unlicense.org> for the full text.
