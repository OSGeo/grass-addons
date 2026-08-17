<!-- markdownlint-disable -->
# Installation

libsixsv has three distinct build paths. The root `Makefile` is the GRASS GIS
build; the standalone commands below build a plain shared library; and
`debian/rules` builds the versioned Debian packages.

## Plain Standalone Build

### Requirements

- A C11 compiler and standard POSIX build tools
- An OpenMP implementation
- `libm`

GCC normally supplies OpenMP through libgomp. Clang commonly requires its
separately packaged OpenMP headers and runtime, such as `libomp-dev` on Debian.
Installing Clang alone does not guarantee that `clang -fopenmp` can compile and
link a program.

From the libsixsv root, build an unversioned development library with GCC:

```sh
gcc -std=c11 -O3 -fPIC -Iinclude -Isrc \
    -Wall -Wextra -Wno-unused-parameter -fopenmp \
    -shared src/*.c -o libsixsv.so \
    -fopenmp -lm
```

The equivalent Clang command is:

```sh
clang -std=c11 -O3 -fPIC -Iinclude -Isrc \
      -Wall -Wextra -Wno-unused-parameter -fopenmp \
      -shared src/*.c -o libsixsv.so \
      -fopenmp -lm
```

The source or object files precede dependent libraries in these commands. This
ordering is also required when linking callers on linkers that process inputs
from left to right.

Install to a chosen prefix if needed:

```sh
PREFIX=/usr/local
install -d "$PREFIX/lib" "$PREFIX/include/sixsv"
install -m 755 libsixsv.so "$PREFIX/lib/"
install -m 644 include/*.h "$PREFIX/include/sixsv/"
```

Compile a caller with the library flags after the source file:

```sh
gcc -std=c11 -I"$PREFIX/include/sixsv" myprogram.c \
    -L"$PREFIX/lib" -lsixsv -lm -o myprogram
```

The public headers do not expose OpenMP declarations, so callers do not need
`-fopenmp` merely to link the installed shared library. Add it when the caller's
own source uses OpenMP. If the prefix is outside the dynamic loader's configured
paths, configure the loader or use an appropriate runtime search path.

### Standalone Test Library

The testsuite Makefile provides another development-only build:

```sh
make -C testsuite lib
```

It writes `testsuite/libsixsv.so`. It is not an install target and does not
produce the versioned Debian ABI files.

## GRASS GIS Build

The root `Makefile` includes GRASS `Lib.make` and builds a GRASS-named shared
library. It is not the standalone Makefile.

```sh
make MODULE_TOPDIR=/path/to/grass
make install MODULE_TOPDIR=/path/to/grass
```

`MODULE_TOPDIR` must identify a configured GRASS source/build tree. The default
is `../grass`, which is useful only when the repositories have that layout.

The install target places:

| Artifact | Destination |
|---|---|
| `libgrass_sixsv.<GRASS-version>.so` | `$GISBASE/lib/` |
| `include/atcorr.h` | `$GISBASE/include/grass/` |
| `include/brdf.h` | `$GISBASE/include/grass/` |

There is no `python/atcorr.py` binding or script install. Python examples load
the C ABI directly with `ctypes`.

The GRASS Makefile currently uses GCC-style `-fopenmp` and links `-lgomp` when
GRASS does not provide an OpenMP library setting. Use GCC by default. A Clang
build requires compatible OpenMP compile and link settings from the local GRASS
configuration; changing only `CC=clang` may still select the wrong runtime.

## Debian Packages

The Debian build uses GCC/OpenMP through the standard Debian toolchain and
produces the SONAME 2 runtime package plus development files:

```sh
dpkg-buildpackage -b -us -uc
sudo dpkg -i ../libsixsv2_*_*.deb ../libsixsv-dev_*_*.deb
```

The root `make deb` target delegates to this command only after its GRASS make
includes can be loaded; use `dpkg-buildpackage` directly for a standalone
package checkout. The resulting packages install:

| Path | Contents |
|---|---|
| `/usr/lib/<multiarch-triplet>/libsixsv.so.2` | Runtime SONAME symlink |
| `/usr/lib/<multiarch-triplet>/libsixsv.so.2.0.0` | Shared library |
| `/usr/lib/<multiarch-triplet>/libsixsv.so` | Development linker symlink |
| `/usr/lib/<multiarch-triplet>/pkgconfig/libsixsv.pc` | pkg-config metadata |
| `/usr/include/sixsv/*.h` | Fourteen installed headers |

The multiarch triplet is generated from `DEB_HOST_MULTIARCH`; it is not fixed to
one CPU architecture. Use pkg-config for downstream builds:

```sh
cc -std=c11 $(pkg-config --cflags libsixsv) myprogram.c \
   $(pkg-config --libs libsixsv) -o myprogram
```

The runtime dependency on the OpenMP implementation is generated from the
built shared library. `libgomp1` is therefore not a source Build-Depends entry.

## Optional libRadtran SRF Path

`atcorr_srf_compute()` invokes libRadtran's `uvspec` at runtime; libRadtran is
not linked into libsixsv. Both `uvspec` and its data directory must be available.
The SRF correction is for the full-column satellite mode. In the anticipated
guarded API, unsupported observer modes return `NULL` rather than applying a
full-column correction to ground or aircraft coefficients. Callers must treat a
`NULL` result as "no SRF correction".

## Optional OpenMP Target Offload

The GRASS Makefile can probe GPU-specific flags or accept an explicit
`OFFLOAD_FLAGS` value. For example:

```sh
make MODULE_TOPDIR=/path/to/grass \
     OFFLOAD_FLAGS="-foffload=nvptx-none -foffload-options=-O3"
```

Clang offload additionally needs a Clang version built with the target backend,
the matching OpenMP offload runtime, and device libraries. GCC offload likewise
needs its target plugin. `--offload-arch=...` or `-foffload=...` is not sufficient
when those components are absent.

Only the OpenMP target regions in the spatial filters and uncertainty routine
are GPU candidates; the radiative-transfer solver stays on the CPU. Standard
OpenMP can execute target regions on the host when no device is selected, but
toolchain configuration and mandatory-offload environment settings can change
that behavior. Validate the intended device on the deployment system rather
than assuming that a successful build implies GPU execution.

## License

libsixsv is licensed under GPL-2.0-or-later. See `LICENSE`. The project retains
explicit attribution to the pinned 6SV2.1 reference source used for validation.
