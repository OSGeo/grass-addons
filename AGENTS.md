# Agent Instructions

## Scope

- Work only within `src/imagery/i.hyper/`.
- Treat this directory as source of truth.
- Do not create or modify files outside this tree unless explicitly requested.
- Do not modify files under `~/.grass8/addons/`; they are development symlink targets.

## Architecture

`i.hyper.atcorr` is a C GRASS addon that bundles `libsixsv` source
(i.pr/r.pi-style) but compiles everything into a single executable for
maximum portability — compatible with `g.extension` on any GRASS installation
(binary or source) and with traditional `make` using a GRASS source tree:

```
src/imagery/i.hyper/
├── Makefile                  (sequential SUBDIRS build)
├── CMakeLists.txt
└── i.hyper.atcorr/           C addon module (single executable)
    ├── main.c                GRASS module entry point (~2700 lines)
    ├── Makefile              Module.make — compiles main.c + libsixsv/src/*.c
    ├── CMakeLists.txt        cmake build_addon — lists all libsixsv sources
    ├── i.hyper.atcorr.html   user manual
    ├── i.hyper.atcorr.md     markdown manual
    ├── README.md
    └── libsixsv/             vendored via git subtree (YannChemin/libsixsv)
        ├── include/          14 public headers
        └── src/              ~40 .c files, a few internal .h files
```

## Development Setup

- `/home/tomazz/work/link-i-hyper-dev.sh` links source modules into the local
  GRASS 8 addon directory. Run after relevant source changes.
- OpenCode runs from an active GRASS session. Confirm with:
  `g.gisenv && g.mapset -p && g.proj -g`
- Development GRASS project: `ihajper`, GIS database `/media/tomazz/Data1/grass-data`,
  mapset `PERMANENT`.
- Environment: GRASS GIS 8.5.0, CRS EPSG:3035 (ETRS89-extended / LAEA Europe).

## Source Repositories

```
https://github.com/YannChemin/libsixsv         (upstream)
https://github.com/YannChemin/i.hyper.atcorr   (upstream — main.c origin)
https://github.com/mazingaro/grass-addons      (our fork, i.hyper.atcorr branch)
https://github.com/OSGeo/grass-addons          (upstream OSGeo)
```

Treat `/home/tomazz/work/atcorr/` as read-only reference trees; do not modify,
build, install, or clean them while working on the addon.

## Subtree Dependencies

`libsixsv/` is vendored via `git subtree` from `YannChemin/libsixsv`.

### Sync libsixsv (when upstream changes)

```sh
git subtree pull \
    --prefix src/imagery/i.hyper/i.hyper.atcorr/libsixsv \
    https://github.com/YannChemin/libsixsv.git main \
    --squash
```

### Sync main.c (when YannChemin/i.hyper.atcorr changes)

```sh
git fetch https://github.com/YannChemin/i.hyper.atcorr.git main
git checkout FETCH_HEAD -- src/imagery/i.hyper/i.hyper.atcorr/main.c
git commit -m "i.hyper.atcorr: sync main.c from YannChemin"
```

### Publishing upstream

Merge `i.hyper.atcorr` → `i.hyper` with `--no-ff`, then PR
`mazingaro/grass-addons:i.hyper` → `OSGeo/grass-addons`.

## External Dependencies

- **libRadtran 2.0.6** with REPTRAN 2024 data is required for Gaussian SRF
  correction. Not vendored — must be pre-installed.
- **Fortran 6SV2.1** (`~/dev/6sV2.1/`) — optional, for cross-validation tests
  only (upstream testsuite).

## Validation

- C compilation: `make MODULE_TOPDIR=/path/to/grass -C src/imagery/i.hyper`
- `g.extension` test: `g.extension i.hyper.atcorr url=<our-fork> branch=i.hyper.atcorr`
- Keep changes focused and avoid unrelated repository-wide cleanup.
