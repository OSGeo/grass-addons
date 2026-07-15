# Agent Instructions

## Scope

- Work only within `src/imagery/i.hyper/`.
- Treat this directory as source of truth.
- Do not create or modify files outside this tree unless explicitly requested.
- Do not modify files under `~/.grass8/addons/`; they are development symlink targets.

## Architecture

`i.hyper.atcorr` is a C GRASS addon following the established `i.pr/PRLIB`
and `r.pi/r.pi.library` precedent — a bundled C library at the parent level
with a `Module.make`-based tool linking against it:

```
src/imagery/i.hyper/
├── Makefile                  (explicit SUBDIRS, libsixsv first, sequential build)
├── CMakeLists.txt
├── libsixsv/                 bundled C library (Lib.make)
│   ├── Makefile              LIB_NAME = grass_sixsv.$(GRASS_LIB_VERSION_NUMBER)
│   ├── CMakeLists.txt
│   ├── include/              14 public headers
│   └── src/                  ~40 .c files, a few internal .h files
├── i.hyper.atcorr/           C addon module (Module.make)
│   ├── main.c                GRASS module entry point (~2700 lines)
│   ├── Makefile              links -lgrass_sixsv, Module.make
│   ├── CMakeLists.txt
│   ├── i.hyper.atcorr.html   user manual
│   ├── i.hyper.atcorr.md     markdown manual
│   ├── README.md
│   ├── INSTALL.md
│   ├── LICENSE               Unlicense (public domain)
│   ├── python/atcorr.py      ctypes bindings to libgrass_sixsv
│   ├── tests/                C and Python unit tests
│   └── testsuite/            comprehensive test suite
└── ... (existing addons unchanged)
```

## Development Setup

- `/home/tomazz/work/link-i-hyper-dev.sh` links source modules into the local
  GRASS 8 addon directory. Run after relevant source changes.
- OpenCode runs from an active GRASS session. Confirm with:
  `g.gisenv && g.mapset -p && g.proj -g`
- Development GRASS project: `ihajper`, GIS database `/media/tomazz/Data1/grass-data`,
  mapset `PERMANENT`.
- Environment: GRASS GIS 8.5.0, CRS EPSG:3035 (ETRS89-extended / LAEA Europe).

## Collaboration Model

- YannChemin is collaborator on `mazingaro/grass-addons`.
- He pushes directly to the `i.hyper.atcorr` branch (no PR needed).
- When features are ready, merge `i.hyper.atcorr` → `i.hyper` with `--no-ff`,
  then PR from `mazingaro/grass-addons:i.hyper` → `OSGeo/grass-addons`.
- He maintains both `libsixsv/` and `i.hyper.atcorr/`.
- Source comparisons are pinned to:
  - `YannChemin/libsixsv` revision `c75c1d82486b942ccddca8052f90bc1d276bbba4`
    https://github.com/YannChemin/libsixsv/tree/c75c1d82486b942ccddca8052f90bc1d276bbba4
  - `YannChemin/i.hyper.atcorr` revision `71404b415ac28c0a1e33a26e3591a23d9b906f64`
    https://github.com/YannChemin/i.hyper.atcorr/tree/71404b415ac28c0a1e33a26e3591a23d9b906f64

## Atmospheric Correction Source Repositories

Treat these paths as read-only reference trees; do not modify, build, install,
or clean them while working on the addon:
  `/home/tomazz/work/atcorr/i.hyper.atcorr`
  `/home/tomazz/work/atcorr/libsixsv`
  `/home/tomazz/work/atcorr/i.atcorr2`

## External Dependencies

- **libRadtran 2.0.6** with REPTRAN 2024 data is required for Gaussian SRF
  correction. Not vendored — must be pre-installed.
- **Fortran 6SV2.1** (`~/dev/6sV2.1/`) — optional, for cross-validation tests
  only (`testsuite/test_fortran_compat.py`).

## Validation

- C compilation: run `make` in the addon directory
- Python syntax: `python -m py_compile src/imagery/i.hyper/i.hyper.atcorr/python/atcorr.py`
- Test suite: `python -m pytest src/imagery/i.hyper/i.hyper.atcorr/testsuite/ -v`
- Fortran compatibility tests require `~/dev/6sV2.1/` objects (optional; skipped
  when absent)
- After source changes and before GRASS-dependent tests:
  `/home/tomazz/work/link-i-hyper-dev.sh`
  Confirm session: `g.gisenv && g.mapset -p && g.proj -g`
- Keep changes focused and avoid unrelated repository-wide cleanup.
