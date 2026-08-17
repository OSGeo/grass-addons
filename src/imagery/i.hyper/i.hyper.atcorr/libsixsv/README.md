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
| Solar irradiance and Earth-Sun distance | `solar.c`, `solar_table.c` | `SOLIRR.f` table port with C interpolation; on-grid samples tested against Fortran |
| Standard continental, maritime, and urban aerosol components | `aerosol_tables.c`, `aerosol.c` | Direct component-table and mixture port; corrected and pipeline-tested against Fortran |
| Scalar scattering solver | `discom.c`, `rt.c`, `scatra.c`, `kernel.c`, `interp.c` | Directly derived from Fortran; pipeline-tested against the pinned executable |
| Gas absorption | `gas_abs.c`, `gas_tables.c` | Direct ABSTRA-derived calculation with separate C path API; tables regenerated from all 256 Fortran intervals and tested in the pipeline |
| Stokes I/Q/U vector result | `trunca.c`, `ospol.c`, `kernelpol.c`, `interp.c` | Full polarized TRUNCA coefficients and aerosol I/Q/U coupling ported; tested for Rayleigh, continental, maritime, and BDM cases |
| Satellite sensor path | `lut.c`, `discom.c` | Corrected to the Fortran `idatmp=4`, full target-to-sensor aerosol/Rayleigh column convention |
| Aircraft sensor path | `pressure.c`, `gas_abs.c`, `scatra.c`, `lut.c` | `PRESPLANE` pressure/gas columns and target-to-aircraft Rayleigh/aerosol paths ported and pipeline-tested at 3 and 10 km |
| `AEROSOL_DESERT` | `aerosol.c`, `aerosol_polar_tables.c` | BDM extinction, scattering, asymmetry, and I/Q/U phase tables ported and pipeline-tested |
| Custom Mie aerosol | `mie.c` | Scalar-only C extension; not equivalent to the complete original 6SV user-defined aerosol workflow |
| AOD x H2O x wavelength LUT | `lut.c`, `correct.c` | C extension built from the ported coefficients |
| Lambertian inversion | `atcorr.c`, `correct.c` | C implementation of the 6SV coefficient equation |
| BRDF, terrain, adjacency, retrieval, OE, uncertainty, spatial filtering | corresponding C modules | Operational C extensions; not direct Fortran 6SV2.1 ports |
| Fine-resolution SRF gas correction | `srf_conv.c` | Guarded off: direction-only factors are incompatible with effective path-gas coefficients |
| OpenMP and GPU directives | LUT and image-level modules | C extension |

The pinned matrix covers representative satellite, aircraft, Rayleigh, continental,
maritime, and BDM cases. It does not exhaustively validate every geometry, profile,
wavelength, custom aerosol, or operational retrieval extension.

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
   -> directional and total-path ABSTRA gas transmission for every H2O/wavelength node
  -> combine scattering and gas transmission
  -> LutArrays: R_atm, T_down, T_up, s_alb
```

The original program computes gas and scattering in one driver. The C LUT computes them
separately while preserving the original nonlinear total-path gas term:

```text
T_down = T_down_scattering * T_down_gas
T_up   = T_up_scattering * T_total_gas / T_down_gas
R_atm  = (R_atm_scattering - R_rayleigh) * T_half_H2O
         + R_rayleigh * T_no_H2O
```

Consequently, the public LUT fields are correction coefficients, not four
independent optical measurements. `R_atm` is the gas-weighted effective path
reflectance. `T_down` contains the solar-path scattering and gas term, while
`T_up` is the effective factor which makes `T_down * T_up` reproduce the
nonlinear total-path gas term in the 6SV surface-coupling equation. `s_alb` is
the scattering spherical albedo.

For a satellite, `taer55p`, `trayp`, and the gas column represent the full column
between the target and sensor, matching the original `idatmp=4` convention.

For an aircraft, the port follows `PRESPLANE.f`: it interpolates the sensor pressure,
integrates the target-to-aircraft gas profile, derives the partial Rayleigh column, and
uses the original exponential default for the partial aerosol optical depth.

`LutConfig.altitude_km` selects the observer mode: values at least 100 km use
the satellite/full-column convention, values above 0 and below 100 km use the
aircraft partial-column convention, and non-positive values use a ground
observer with no target-to-sensor path. Surface elevation is not encoded by
this selector; set `surface_pressure` when the target pressure differs from the
selected standard atmosphere.

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

The BDM desert model uses its independent extinction, scattering, asymmetry, PHA, QHA,
and UHA tables from `BDM.f`; it is not synthesized from the standard component mixture.
The polarized path also retains signed Q/U interpolation and the complete `TRUNCA.f`
`alpha`, `beta`, `gamma`, and `zeta` expansions.

### Gas workflow

The gas path follows the relevant `ABSTRA.f` operations:

```text
wavelength -> wavenumber and one of six 256-interval tables
  -> gas-specific Curtis-Godson coefficients
  -> trapezoidal pressure/profile column integration
  -> H2O/CO2/O2/N2O/CH4/CO transmittance
  -> independent visible ozone continuum transmittance
  -> gas-species transmittances for solar, view, and nonlinear total paths
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
9. Ported the BDM desert optical and polarized phase tables instead of substituting the
   continental mixture.
10. Restored aerosol Stokes Q/U phase matrices, polarized TRUNCA coefficients, and
    I/Q/U multiple-scattering coupling.
11. Ported `PRESPLANE` and target-to-aircraft gas, Rayleigh, and aerosol columns.
12. Restored ABSTRA total-path gas transmission in the effective Lambertian LUT
    coefficients, including strong water-vapor absorption bands.

## Pipeline parity results

The satellite fixture uses SZA 30 degrees, nadir view, continental aerosol, AOD 0.2,
H2O 2.0 g/cm2, ozone 300 DU, and a Lambertian reflectance of 0.20. `R_atm` and `T_up`
below are the effective coefficients that reproduce the original 6SV surface-coupling
equation.

| nm | Coefficient | Fortran | C | Relative error |
|---:|---|---:|---:|---:|
| 450 | R_atm | 0.099514 | 0.099491 | -0.023% |
| 450 | T_down | 0.829247 | 0.829959 | +0.086% |
| 450 | T_up | 0.852080 | 0.848949 | -0.368% |
| 450 | s_alb | 0.190940 | 0.190817 | -0.064% |
| 550 | R_atm | 0.046894 | 0.046896 | +0.005% |
| 550 | T_down | 0.871633 | 0.872271 | +0.073% |
| 550 | T_up | 0.890349 | 0.887237 | -0.349% |
| 550 | s_alb | 0.120280 | 0.120112 | -0.140% |
| 650 | R_atm | 0.027515 | 0.027523 | +0.031% |
| 650 | T_down | 0.900106 | 0.900678 | +0.064% |
| 650 | T_up | 0.916090 | 0.913232 | -0.312% |
| 650 | s_alb | 0.084630 | 0.084439 | -0.226% |
| 850 | R_atm | 0.013153 | 0.013158 | +0.037% |
| 850 | T_down | 0.950123 | 0.950580 | +0.048% |
| 850 | T_up | 0.958714 | 0.956443 | -0.237% |
| 850 | s_alb | 0.050300 | 0.050094 | -0.410% |

Passing the original Fortran apparent reflectances through the C coefficients recovers
`0.200579`, `0.200545`, `0.200488`, and `0.200378` at 450, 550, 650, and 850 nm.

At 550 nm with SZA 30 degrees, VZA 40 degrees, and relative azimuth 300 degrees, the
polarized path gives:

| Model | Fortran I/Q/U | C I/Q/U |
|---|---|---|
| Rayleigh | 0.04722 / 0.00163 / 0.00855 | 0.047318 / 0.001639 / 0.008566 |
| Continental | 0.06235 / 0.00135 / 0.00718 | 0.062421 / 0.001357 / 0.007191 |
| Maritime | 0.06424 / 0.00190 / 0.01035 | 0.064354 / 0.001908 / 0.010369 |
| BDM desert | 0.06394 / 0.00112 / 0.00587 | 0.063996 / 0.001119 / 0.005882 |

Aircraft cases at 3 and 10 km are tested at 550 and 940 nm. Their atmospheric path,
Q/U, downward and effective upward transmission, and spherical albedo agree within the
fixture tolerances, including the 940 nm water-vapor absorption band. No empirical
calibration factors are applied.

Additional fixtures verify zero I/Q/U path coefficients for a ground observer, a
gas-weighted polarized satellite case at 940 nm, and the 3.75 µm H2O continuum. At
3.75 µm the C directional coefficients remain within 4% of the pinned executable; the
effective path coefficient differs by about `1.0e-4` in absolute reflectance.

## Features

- **Radiative transfer solver**: DISCOM discrete-ordinate method (up to 20 scattering
  orders), with validated scalar and vector Stokes I/Q/U output
- **3-D look-up table** computation over [AOD × H₂O × wavelength]
- **Atmospheric correction primitives**: scalar Lambertian inversion and an
  explicit BRDF/albedo-coupled inversion helper
- **Scene-based automatic retrievals**
  - Water vapour (H₂O) from 940 nm band depth or triplet
  - Aerosol optical depth (AOD) via MODIS dark-dense-vegetation (DDV) and spatial
    regularisation (MAIAC-inspired)
  - Ozone from Chappuis 600 nm band
  - Surface pressure from O₂-A 760 nm or ISA elevation
- **Joint AOD + H₂O optimal estimation** (MAP grid-search + refinement)
- **BRDF surface models**: Lambertian, Rahman (RPV), Roujean, Hapke, ocean,
  Walthall, Minnaert and one Ross-Li-Maignan implementation; NBAR
  normalisation and MCD43 disaggregation (`BRDF_VERSFELD` and `BRDF_IAPI` are
  reserved stubs)
- **Topographic correction** — illumination angle and transmittance
- **Adjacency approximation**: box-filtered environmental reflectance with a
  Beer-Lambert direct-path estimate following the 6S/Vermote formulation
- **Uncertainty propagation** — instrument noise and AOD perturbation
- **SRF guard** prevents direction-only gas factors from corrupting effective
  path-gas coefficients
- **OpenMP parallelisation** in selected bulk operations

`AEROSOL_CUSTOM` computes a scalar log-normal Mie aerosol. It has no supported
custom polarized phase matrix. The guarded API rejects custom Mie together with
`enable_polar=1` rather than returning unsupported Q/U values. Likewise,
`atcorr_srf_compute()` currently always returns `NULL`, and
`atcorr_srf_apply()` is a guarded no-op. Joint convolution must update effective
I/Q/U path terms and nonlinear total gas transmission together before this API
can be enabled safely.

## Parallelism with OpenMP

OpenMP is used by specific bulk routines; it is not a blanket property of every
public call. In particular, `atcorr_invert()` and `atcorr_invert_brdf()` are
single-value inline functions, so callers own any enclosing pixel loop.

| Workload | Parallelisation strategy |
|---|---|
| `atcorr_compute_lut()` | AOD nodes; each worker owns a `SixsCtx` |
| Joint AOD/H₂O and selected retrieval/surface routines | Pixel loops |
| Adjacency correction | Final pixel correction loop; neighbourhood filtering is handled separately |
| Spatial box/Gaussian filters | OpenMP target teams over the two passes |
| Uncertainty propagation | OpenMP target teams over pixels |

The CPU thread count can be controlled with the standard OpenMP environment
variable:

```sh
export OMP_NUM_THREADS=16   # use 16 cores
```

### GPU offload via OpenMP target

Only spatial filtering and uncertainty contain OpenMP target regions. The
radiative-transfer solver remains on the CPU. GPU execution additionally needs
a compiler target backend, matching OpenMP offload runtime and device libraries;
accepting an offload flag does not prove that a device was used. Standard
OpenMP host fallback may apply when no device is selected, but runtime settings
such as mandatory offload can make absence of a device an error. See
`INSTALL.md` and validate the deployment toolchain explicitly.

## Aerosol and atmosphere models

| Identifier            | Description                  |
|-----------------------|------------------------------|
| `AEROSOL_NONE`        | Rayleigh scattering only      |
| `AEROSOL_CONTINENTAL` | Continental mixture           |
| `AEROSOL_MARITIME`    | Maritime mixture              |
| `AEROSOL_URBAN`       | Urban mixture                 |
| `AEROSOL_DESERT`      | Desert dust                   |
| `AEROSOL_CUSTOM`      | Custom Mie log-normal (scalar only) |

| Identifier    | Description                 |
|---------------|-----------------------------|
| `ATMO_US62`   | US Standard Atmosphere 1962 |
| `ATMO_MIDSUM`    | Mid-latitude summer      |
| `ATMO_MIDWIN`    | Mid-latitude winter      |
| `ATMO_TROPICAL`  | Tropical                 |
| `ATMO_SUBSUM`    | Sub-arctic summer        |
| `ATMO_SUBWIN`    | Sub-arctic winter        |

## Public API

The Debian development package installs fourteen headers to
`/usr/include/sixsv/`. The GRASS install is narrower: it exposes only the
module-facing `atcorr.h` and `brdf.h` under `include/grass/`.

| Header              | Purpose                                      |
|---------------------|----------------------------------------------|
| `atcorr.h`          | LUT computation and per-pixel inversion       |
| `brdf.h`            | BRDF model evaluation and NBAR normalisation  |
| `retrieve.h`        | Scene-based retrieval algorithms              |
| `oe_invert.h`       | Joint AOD + H₂O optimal estimation            |
| `adjacency.h`       | Environmental-reflectance adjacency helper    |
| `terrain.h`         | Topographic corrections                       |
| `uncertainty.h`     | Noise and AOD uncertainty propagation         |
| `spatial.h`         | Gaussian and box filtering (NaN-safe)         |
| `surface_model.h`   | 3-component surface prior (VEG/SOIL/WATER)    |
| `spectral_brdf.h`   | MCD43 disaggregation and spectral smoothing   |
| `sixs_ctx.h`        | Low-level 6SV computation context              |
| `aerosol_tables.h`  | Generated aerosol table declarations          |
| `gas_tables.h`      | Generated gas table declarations              |
| `solar_table.h`     | Generated `SOLIRR.f` table declaration         |

The Debian runtime package is `libsixsv2`, reflecting the `libsixsv.so.2` C
ABI. `LutConfig`, `LutArrays`, `BrdfParams` and `SixsCtx` layouts are ABI data;
direct `ctypes` users must mirror the installed SONAME 2 headers exactly. The
project does not install or version a Python wrapper API.

## Installing the Debian package

Build and install the packages with:

```sh
dpkg-buildpackage -us -uc -b
sudo dpkg -i ../libsixsv2_*.deb ../libsixsv-dev_*.deb
```

After installation:

- Headers: `/usr/include/sixsv/` (`atcorr.h`, `brdf.h`, `retrieve.h`, …)
- Library: `/usr/lib/<multiarch-triplet>/libsixsv.so.2`
- Development symlink: `/usr/lib/<multiarch-triplet>/libsixsv.so`
- pkg-config: `/usr/lib/<multiarch-triplet>/pkgconfig/libsixsv.pc`

`<multiarch-triplet>` is generated from `DEB_HOST_MULTIARCH`, not hardcoded to
one architecture.

For the **Debian standalone build** of
[i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr), also install
[libras3d-dev](https://github.com/yannchemin/libras3d) — the GRASS API
replacement that routes cube I/O through libtiff/libgeotiff and libhdf5.

## Compiling against the installed library

Use pkg-config and place its linker flags after the source file:

```sh
cc -std=c11 -O2 $(pkg-config --cflags libsixsv) my_program.c \
   $(pkg-config --libs libsixsv) -o my_program
```

The shared library records its OpenMP runtime dependency. A caller needs its
own OpenMP compiler flag only if the caller source contains OpenMP constructs.

## Python (ctypes)

The examples load the C ABI directly; no `atcorr.py` wrapper is installed:

```python
import ctypes, ctypes.util
path = ctypes.util.find_library("sixsv")
if path is None:
    raise RuntimeError("libsixsv is not installed in the loader search path")
lib = ctypes.CDLL(path)
```

See `examples/README.md` for the source-tree `LIB_SIXSV` override and ABI
layout caveats.

## Validation

The portable/public validation path uses the committed fixtures and does not
require a private checkout of 6SV2.1:

```sh
make -C testsuite lib
LIB_SIXSV="$PWD/testsuite/libsixsv.so" python3 -m pytest -v \
    testsuite/test_lut.py testsuite/test_solar.py \
    testsuite/test_openmp.py \
    testsuite/test_6sv21_pipeline_parity.py \
    testsuite/test_6sv21_extended_parity.py
```

This path needs Python 3, NumPy and pytest in addition to the C/OpenMP build
dependencies. The OpenMP tests check serial/parallel consistency and host
results for target-annotated routines; they do not prove that a physical GPU
executed the target regions.

Local reference regeneration and direct Fortran subroutine comparison are a
separate maintainer workflow. They require gfortran and the pinned 6SV2.1 source
at commit `7deb2289cfe23c9b1d1b48d7647f76604ef75fa4`, supplied through `SIXSV2`.
`make -C testsuite test` belongs to that local workflow because its Fortran
driver target consumes objects from the reference tree. Debian package builds
deliberately skip both paths; pytest, NumPy and the pinned Fortran tree are not
package Build-Depends.

## Dependencies

## Runtime

- C standard library (`libm`)
- OpenMP runtime selected by the compiler
- libRadtran is not currently used because SRF correction is guarded off

## Build

- C11-capable compiler with OpenMP support
- GRASS GIS development environment for the GRASS build; standard POSIX tools
  for the plain standalone build
- Python 3, NumPy and pytest for the public test path; gfortran and the pinned
  6SV2.1 source only for local reference validation

## Related repositories

| Repository                                                          | Relationship           | Description |
|---------------------------------------------------------------------|------------------------|-------------|
| [i.hyper.atcorr](https://github.com/yannchemin/i.hyper.atcorr)       | **Downstream consumer** | GRASS GIS module that links libsixsv for 6SV2.1 atmospheric correction of hyperspectral cubes |
| [libras3d](https://github.com/yannchemin/libras3d) | **Peer — Debian standalone** | Drop-in GRASS raster3d API replacement; used alongside libsixsv when building i.hyper.atcorr without GRASS (`DEBIAN_BUILD=1`) |

## License

libsixsv is licensed under the GNU General Public License, version 2 or later
(`GPL-2.0-or-later`). See `LICENSE`. The pinned 6SV2.1 provenance and routine
attribution are retained independently of the project license declaration.
