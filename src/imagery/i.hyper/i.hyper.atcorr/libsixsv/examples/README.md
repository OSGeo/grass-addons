<!-- markdownlint-disable -->
# libsixsv API Examples

The directory contains paired C and Python demonstrations. The Python files are
not clients of an installed wrapper module: each declares the required C ABI
with `ctypes` and uses NumPy arrays for storage.

## Examples

| Pair | Demonstrates |
|---|---|
| `01_basic_lut` | LUT allocation/computation, spectral slicing, Lambertian inversion, solar irradiance and Earth-Sun distance |
| `02_scene_correction` | Spatially varying LUT interpolation, polarized output and BRDF-coupled inversion |
| `03_retrievals` | H2O, AOD, ozone and pressure retrieval helpers, quality masks and joint inversion |
| `04_brdf` | RPV, Ross-Li-Maignan and Hapke evaluation, hemispherical integration, NBAR and MCD43 disaggregation |
| `05_spatial_filters` | Spatial filters, terrain helpers, adjacency correction and uncertainty propagation |
| `06_full_pipeline` | An illustrative synthetic scene pipeline combining the APIs above |

The operational retrieval, BRDF, terrain, adjacency, uncertainty and spatial
APIs are C extensions. They are not all direct ports of 6SV2.1 and should not be
interpreted as independently validated remote-sensing products merely because
an example completes.

## Build And Run C Examples

Build the development library first, then compile the examples:

```sh
make -C testsuite lib
make -C examples
make -C examples run
```

The example Makefile keeps the source/object before `-lsixsv`, which is required
for correct linker resolution. It embeds a development rpath to
`testsuite/libsixsv.so`; installed applications should use pkg-config or their
normal build system instead.

## Run Python Examples

Requirements are Python 3 and NumPy. Build the test library and run a script:

```sh
make -C testsuite lib
python3 examples/01_basic_lut.py
```

Each script searches, in order:

1. The file named by `LIB_SIXSV`, when set.
2. `testsuite/libsixsv.so` relative to the source tree.

For example:

```sh
LIB_SIXSV=/opt/libsixsv/lib/libsixsv.so python3 examples/01_basic_lut.py
```

The scripts define `ctypes.Structure` layouts that must match the SONAME 2
headers exactly. They are examples, not a stable Python package. Prefer a small
application-owned binding layer and verify the loaded `atcorr_version()` when
integrating the ABI into a Python application.

## Important API Semantics

- `LutConfig.altitude_km >= 100` selects the full-column satellite path;
  `0 < altitude_km < 100` selects an aircraft path; non-positive values select
  a ground observer. Surface elevation is represented separately through
  `surface_pressure`.
- `R_atm` is the gas-weighted effective atmospheric path reflectance and `T_up`
  is the effective factor used with `T_down` in the 6SV Lambertian coupling
  equation. Do not reinterpret `T_up` as a separately computed directional gas
  transmittance.
- `AEROSOL_CUSTOM` uses the custom log-normal Mie calculation only in scalar
  mode. Combining it with `enable_polar=1` is
  rejected rather than returning unsupported custom-aerosol Q/U values.
- SRF/libRadtran correction is guarded off because direction-only factors cannot
  be multiplied into gas-weighted effective coefficients consistently.
- `BrdfType` provides one Ross-Li implementation,
  `BRDF_ROSSLIMAIGNAN`. `BRDF_VERSFELD` and `BRDF_IAPI` remain stubs. BRDF model
  fields in `LutConfig` do not make `atcorr_compute_lut()` perform a BRDF
  inversion; evaluate the BRDF/albedo and call the BRDF inversion API explicitly.
- `adjacency_correct_band()` expects a two-way total scattering transmittance in
  `T_scat`; it derives and subtracts the direct component internally. A one-way
  diffuse term such as `1 - T_down_dir` is not equivalent.
- `sixs_E0()` linearly interpolates the table ported from 6SV2.1 `SOLIRR.f`.
  It is not an SRF-integrated band irradiance; applications with measured SRFs
  should perform their own convolution.

## Output And Validation

The programs print diagnostics for their synthetic inputs. No fixed expected
output is documented here because coefficient changes, compiler precision and
OpenMP reduction order can alter printed values without changing the API
demonstration. Numerical acceptance criteria belong in `testsuite/`, including
the committed pinned-reference fixtures, rather than in example transcripts.
