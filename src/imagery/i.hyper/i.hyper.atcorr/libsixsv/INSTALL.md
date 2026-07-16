# Installation

## 1. Installation inside GRASS GIS

### Prerequisites

- GRASS GIS source tree checked out and compiled (the library expects the source
  tree at `../grass` relative to this directory, or you can override `MODULE_TOPDIR`)
- C11-capable compiler (GCC ≥ 5 or Clang ≥ 6)
- OpenMP support in the compiler (`-fopenmp`)

### Build and install

```sh
# From the lib6sv directory
make MODULE_TOPDIR=/path/to/grass   # defaults to ../grass

# Install into the running GRASS installation
make install MODULE_TOPDIR=/path/to/grass
```

`make install` copies three artifacts into the GRASS installation tree
(`$INST_DIR`, which corresponds to `$GISBASE`):

| Artifact | Destination |
|----------|-------------|
| `libgrass_sixsv.<version>.so` | `$GISBASE/lib/` |
| `include/atcorr.h` | `$GISBASE/include/grass/` |
| `include/brdf.h`   | `$GISBASE/include/grass/` |
| `python/atcorr.py` | `$GISBASE/scripts/` |

After installation, the library is loadable by any GRASS module that links with
`-lgrass_sixsv.<version>` and includes `<grass/atcorr.h>`.

### Optional: GPU offload (GRASS build)

Add `OFFLOAD_FLAGS` to the make invocation.  The pixel-level loops in
`uncertainty.c` and `spatial.c` will be offloaded to the GPU; everything else
continues to run on the CPU.  No source changes are needed.

```sh
# GCC + NVIDIA GPU (requires GCC built with --enable-offload-targets=nvptx-none)
make OFFLOAD_FLAGS="-foffload=nvptx-none -foffload-options=-O3" \
     MODULE_TOPDIR=/path/to/grass

# Clang + NVIDIA GPU
make CC=clang OFFLOAD_FLAGS="--offload-arch=sm_75" \
     MODULE_TOPDIR=/path/to/grass

# Clang + AMD GPU
make CC=clang OFFLOAD_FLAGS="--offload-arch=gfx908" \
     MODULE_TOPDIR=/path/to/grass
```

When no GPU is present at runtime, the OpenMP target directives fall back
silently to host (CPU) execution.

### Optional: SRF gas-transmittance support

The `atcorr_srf_compute()` function requires the **libRadtran** `uvspec` binary on
`PATH`.  Install libRadtran separately and make sure `uvspec` is accessible before
calling that function.

---

## 2. Standalone installation

The C sources have **zero GRASS dependencies** at compile time.  You can build the
shared library independently with a plain Makefile or directly with the compiler.

### Prerequisites

- C11-capable compiler (GCC ≥ 5 or Clang ≥ 6)
- OpenMP (`-fopenmp`)
- `libm`

### Build

```sh
# Collect all sources
SRC=$(ls src/*.c)

# Compile to a shared library
gcc -std=c11 -O3 -ffast-math -fPIC \
    -Iinclude -Isrc \
    -Wall -Wextra -Wno-unused-parameter \
    -fopenmp \
    -shared -o libsixsv.so \
    $SRC \
    -lm
```

Or with Clang:

```sh
clang -std=c11 -O3 -ffast-math -fPIC \
    -Iinclude -Isrc \
    -Wall -Wextra -Wno-unused-parameter \
    -fopenmp \
    -shared -o libsixsv.so \
    $SRC \
    -lm
```

### Install to a prefix

```sh
PREFIX=/usr/local   # or ~/.local, /opt/sixsv, …

install -d $PREFIX/lib $PREFIX/include/sixsv
install -m 755 libsixsv.so $PREFIX/lib/
install -m 644 include/*.h  $PREFIX/include/sixsv/
```

Then compile your own code against the library:

```sh
gcc -std=c11 -I$PREFIX/include/sixsv \
    -L$PREFIX/lib -lsixsv \
    -fopenmp -lm \
    -o myprogram myprogram.c
```

If `$PREFIX` is not a standard system path, set the runtime search path:

```sh
export LD_LIBRARY_PATH=$PREFIX/lib:$LD_LIBRARY_PATH
# or link with:  -Wl,-rpath,$PREFIX/lib
```

### Optional: GPU offload (standalone build)

Add the offload flags directly to the compiler invocation:

```sh
# GCC + NVIDIA GPU
gcc -std=c11 -O3 -ffast-math -fPIC \
    -Iinclude -Isrc \
    -fopenmp -foffload=nvptx-none -foffload-options="-O3" \
    -shared -o libsixsv.so $SRC -lm

# Clang + NVIDIA GPU
clang -std=c11 -O3 -ffast-math -fPIC \
    -Iinclude -Isrc \
    -fopenmp --offload-arch=sm_75 \
    -shared -o libsixsv.so $SRC -lm

# Clang + AMD GPU
clang -std=c11 -O3 -ffast-math -fPIC \
    -Iinclude -Isrc \
    -fopenmp --offload-arch=gfx908 \
    -shared -o libsixsv.so $SRC -lm
```

### Optional: SRF gas-transmittance support

Same as for the GRASS build: install libRadtran and ensure `uvspec` is on `PATH`
before calling `atcorr_srf_compute()`.

---

## 3. Debian package

Build and install a native `.deb` for Debian trixie (or any debhelper 13 system):

```sh
cd libsixsv
dpkg-buildpackage -b -us -uc

# Packages appear one level up:
sudo dpkg -i ../libsixsv1_1.0.0-1_amd64.deb \
              ../libsixsv-dev_1.0.0-1_amd64.deb
```

The `libsixsv-dev` package installs:

| Path | Contents |
|---|---|
| `/usr/lib/x86_64-linux-gnu/libsixsv.so` | Development symlink |
| `/usr/include/sixsv/*.h` | All 14 public headers |
| `/usr/lib/x86_64-linux-gnu/pkgconfig/libsixsv.pc` | pkg-config file |

After installation, downstream projects can use pkg-config:

```sh
pkg-config --cflags libsixsv   # → -I/usr/include/sixsv
pkg-config --libs   libsixsv   # → -lsixsv
```

To uninstall:

```sh
sudo apt-get remove libsixsv1 libsixsv-dev
```

## License

This is free and unencumbered software released into the public domain.  
See <https://unlicense.org> for the full text.
