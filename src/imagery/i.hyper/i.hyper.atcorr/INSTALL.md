# Installation

## Quick reference

| Mode | Command | Requires |
|---|---|---|
| GRASS module | `make` | GRASS GIS source + libsixsv (GRASS build) |
| Debian standalone | `make DEBIAN_BUILD=1` | libras3d-dev + libsixsv-dev (.deb) |

---

## 1. GRASS GIS module

### 1a. Dependencies

- GRASS GIS 8.x source tree (default path: `$HOME/dev/grass`)
- GCC ≥ 5 or Clang ≥ 6 with OpenMP
- `libsixsv` built and installed into the GRASS tree (see step 1b)

### 1b. Build and install libsixsv (GRASS flavour)

```sh
cd ~/dev/libsixsv
make MODULE_TOPDIR=$HOME/dev/grass
sudo make install MODULE_TOPDIR=$HOME/dev/grass
```

This installs `libgrass_sixsv.<version>.so` into `$GISBASE/lib/` and
`atcorr.h` / `brdf.h` into `$GISBASE/include/grass/`.

### 1c. Build the module

```sh
cd ~/dev/i.hyper.atcorr
make                               # uses MODULE_TOPDIR=$HOME/dev/grass
```

The compiled binary appears at `dist.x86_64-pc-linux-gnu/bin/i.hyper.atcorr`.

### 1d. Install into a running GRASS

```sh
# Copy binary and library to your GRASS installation
sudo cp dist.*/bin/i.hyper.atcorr          /usr/local/grass*/bin/
sudo cp dist.*/lib/libgrass_sixsv.*.so     /usr/local/grass*/lib/
```

Or use the standard GRASS module install target:

```sh
make install MODULE_TOPDIR=$HOME/dev/grass
```

---

## 2. Debian standalone binary (`DEBIAN_BUILD=1`)

Produces a self-contained binary that reads GeoTIFF and HDF5 hyperspectral
cubes directly, with no GRASS GIS required.

### 2a. Install Debian packages

Build the packages from source if you do not have pre-built `.deb` files:

```sh
# libsixsv
cd ~/dev/libsixsv && dpkg-buildpackage -b -us -uc
sudo dpkg -i ../libsixsv1_1.0.0-1_amd64.deb \
              ../libsixsv-dev_1.0.0-1_amd64.deb

# libras3d
cd ~/dev/ras3d && dpkg-buildpackage -b -us -uc
sudo dpkg -i ../libras3d_0.1.0-1_amd64.deb \
              ../libras3d-dev_0.1.0-1_amd64.deb
```

Or install pre-built packages if available:

```sh
sudo dpkg -i libsixsv1_1.0.0-1_amd64.deb \
              libsixsv-dev_1.0.0-1_amd64.deb \
              libras3d_0.1.0-1_amd64.deb \
              libras3d-dev_0.1.0-1_amd64.deb
```

### 2b. Build

```sh
cd ~/dev/i.hyper.atcorr
make DEBIAN_BUILD=1
```

The Makefile uses `pkg-config` for both `libras3d` and `libsixsv` and
auto-detects the correct HDF5 library name (`libhdf5_serial` on Debian
trixie).  To override:

```sh
make DEBIAN_BUILD=1 CC=clang CFLAGS="-O3 -ffast-math"
```

### 2c. Install

```sh
# Default: /usr/local/bin/i.hyper.atcorr
sudo make DEBIAN_BUILD=1 install

# Custom prefix
sudo make DEBIAN_BUILD=1 PREFIX=/opt/hyper install
```

### 2d. Run

No GRASS session needed.  Point to input files via environment variables or
full paths:

```sh
# By full path
i.hyper.atcorr \
    input=/data/wyvern.tiff \
    output=/out/wyvern_boa \
    sza=35.2 doy=221

# By name, searched in RAS3D_PATH
export RAS3D_PATH=/data/scenes
export RAS3D_OUTDIR=/out
i.hyper.atcorr input=wyvern output=wyvern_boa sza=35.2 doy=221

# HDF5 Tanager scene (auto-probes for radiance dataset)
i.hyper.atcorr \
    input=/data/20250321_054913_40_4001_basic_radiance_hdf5.h5 \
    output=/out/kanpur_boa \
    sza=42.1 doy=80

# Override HDF5 dataset path
export RAS3D_HDF5_DATASET="/HDFEOS/SWATHS/HYP/Data Fields/toa_radiance"
i.hyper.atcorr input=scene.h5 output=scene_boa sza=42.1 doy=80
```

### 2e. Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `RAS3D_PATH` | — | Directory searched for input maps by name |
| `RAS3D_OUTDIR` | — | Directory for output GeoTIFF files |
| `RAS3D_HDF5_DATASET` | auto | HDF5 dataset path (overrides auto-probe) |
| `RAS3D_VERBOSE` | `1` | Verbosity: 0 quiet, 1 normal, 2 debug |
| `GISDBASE` | `.` | Emulated GRASS gisdbase (for wavelength sidecar paths) |

---

## 3. Uninstall

### GRASS module

```sh
rm -f "$(grass --config path)/bin/i.hyper.atcorr"
```

### Debian standalone

```sh
sudo rm -f /usr/local/bin/i.hyper.atcorr
# optionally remove the libraries:
sudo apt-get remove libras3d libras3d-dev libsixsv1 libsixsv-dev
```

## License

This is free and unencumbered software released into the public domain.  
See <https://unlicense.org> for the full text.
