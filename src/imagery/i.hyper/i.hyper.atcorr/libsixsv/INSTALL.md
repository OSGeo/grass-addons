<!-- markdownlint-disable -->
# Installation

The `libsixsv` sources in `src/` are compiled directly into the GRASS
`i.hyper.atcorr` module by the module build. There is no separate library
installation step for GRASS use.

## Requirements

- A C11 compiler and standard POSIX build tools
- An OpenMP implementation (optional; without it the module builds a serial
  CPU-only variant)
- `libm`
- A configured GRASS source/build tree for the module build, or a running
  GRASS session for installation with `g.extension`

GCC normally supplies OpenMP through libgomp. Clang commonly requires its
separately packaged OpenMP headers and runtime, such as `libomp-dev` on Debian.
Installing Clang alone does not guarantee that `clang -fopenmp` can compile and
link a program.

## GRASS module build

Build and install `i.hyper.atcorr` (which includes the `libsixsv` sources)
from the module directory, either against a configured GRASS tree:

```sh
make MODULE_TOPDIR=/path/to/grass
```

or into a running GRASS session directly from the local source directory:

```sh
g.extension extension=i.hyper.atcorr url=<addons>/src/imagery/i.hyper/i.hyper.atcorr
```

OpenMP support follows the GRASS configuration: the module uses
`$(OPENMP_CFLAGS)` / `$(OPENMP_INCPATH)` / `$(OPENMP_LIBPATH)` /
`$(OPENMP_LIB)` from GRASS `Platform.make`. When GRASS itself was built
without OpenMP, the module builds a CPU-only variant (the sources guard
parallel regions with `#ifdef _OPENMP`).

There is no `python/atcorr.py` binding or script install.

## Validation test library

The `developer_tests/` directory builds a validation-only shared library:

```sh
make -C developer_tests lib
```

It writes `developer_tests/libsixsv.so`, used solely by the parity tests
(see "Validation" in `README.md`). It is not installed and it is not linked
by the GRASS module.

## Spectral Response Correction

Automatic libRadtran/reptran correction is currently unsupported.
`atcorr_srf_compute()` reports that state and returns `NULL`, while
`atcorr_srf_apply()` leaves the LUT unchanged. Direction-only correction factors
cannot be applied consistently to the gas-weighted effective coefficients used
by the public LUT API. libRadtran is therefore not a runtime dependency.

## OpenMP target offload

The module build does not wire GPU offload flags: only the CPU OpenMP
parallelism from the GRASS configuration is used. `developer_tests/` accepts a
manual `OFFLOAD_FLAGS` override for experiments:

```sh
make -C developer_tests test-openmp OFFLOAD_FLAGS="--offload-arch=sm_86"
```

Clang offload additionally needs a Clang version built with the target backend,
the matching OpenMP offload runtime, and device libraries. `--offload-arch=...`
is not sufficient when those components are absent.

Only the OpenMP target regions in the spatial filters and uncertainty routine
are GPU candidates; the radiative-transfer solver stays on the CPU. Standard
OpenMP can execute target regions on the host when no device is selected, but
toolchain configuration and mandatory-offload environment settings can change
that behavior. Validate the intended device on the deployment system rather
than assuming that a successful build implies GPU execution.

## License

libsixsv is licensed under GPL-2.0-or-later. See `LICENSE`. The project retains
explicit attribution to the pinned 6SV2.1 reference source used for validation.
