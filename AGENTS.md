# AGENTS.md

Instructions for AI assistants and agents working with code in this
repository.

After writing or modifying code, self-review it as a human PR reviewer
would: Is every line needed and justified? Will it be hard to maintain?
Do not present code you cannot explain. When generating substantial
algorithms or logic, note this to the human so they can disclose it in the
commit message or pull request. See the GRASS core
[AI use policy](https://github.com/OSGeo/grass/blob/main/CONTRIBUTING.md#ai-use-policy).

## Relationship to GRASS core

This repository holds **addons**: optional, community-maintained GRASS tools
installed by users with *g.extension*. They depend on a GRASS installation
but are built and released separately from core. As far as AI-assisted coding
is concerned, addons are held to the same quality standards as core tools
(a tool may later graduate into the core repository).

**All core conventions apply here.** Rather than repeat them, this file
documents only what is specific to addons. For everything else, follow:

- [GRASS core `AGENTS.md`](https://github.com/OSGeo/grass/blob/main/AGENTS.md)
  — coding conventions, tool structure, documentation rules, commit messages,
  and how to write tests (`grass.tools`, fixtures, test data patterns).
- [Programming Style Guide](https://github.com/OSGeo/grass/blob/main/doc/development/style_guide.md)
  — full formatting and style rules.

The development branch is `grass8`. The git/fork/PR workflow is in
[`CONTRIBUTING.md`](CONTRIBUTING.md); do not re-derive it.
Having the [core repo](https://github.com/OSGeo/grass/) locally at hand
is helpful for checking against the established conventions and already
available functions to avoid code duplication.

## Creating a new tool

Scaffold new addons with the
[grass-addon-cookiecutter](https://github.com/OSGeo/grass-addon-cookiecutter)
template rather than copying files by hand. It generates the standard layout
(`<name>.py` script, `Makefile`, `<name>.md` with synced `<name>.html`, and a
gunittest `testsuite/`) with the correct naming. It does not generate a
`CMakeLists.txt`; copy one from an existing addon, because *g.extension*
reads the tool name from `project(<name>)` there when GRASS is built with
CMake. New tests are preferably pytest in a `tests/` directory (see "Testing"
below), although using the scaffolded `testsuite/` is acceptable when the NC
SPM sample dataset is used.

Tools live under `src/<category>/<tool>/`, where `<category>` is `raster`,
`vector`, `imagery`, `temporal`, `raster3d`, `display`, `general`, `db`,
`gui`, `misc`, `models`, or `tools`. The tool name prefix must match its
category (`r.*`, `v.*`, `i.*`, `t.*`, `r3.*`, `d.*`, `g.*`, `db.*`, `m.*`).
An addon directory has the same structure as a core tool (see the core
`AGENTS.md` "Tool Structure" section): `<name>.py` or `main.c`, a `Makefile`,
a `CMakeLists.txt`, `<name>.md` (with synced `<name>.html`), and tests in
`tests/` or `testsuite/`.

## Building and installing a single addon

Two paths, depending on what you need:

**Compile against an installed GRASS** (what CI does). `MODULE_TOPDIR` must
point to the GISBASE of an **Autotools** install (the path from
`grass --config path`). This builds and installs the addon into that GRASS
tree:

```bash
cd src/raster/r.example
make MODULE_TOPDIR="$(grass --config path)"
```

**Install into a GRASS session for interactive use or testing**, directly
from the local source directory:

```bash
grass --tmp-project XY --exec \
  g.extension extension=r.example url=$PWD/src/raster/r.example
```

For a **CMake** install, the core source code needs to be installed,
not just compiled, for *g.extension* to work.

## Testing

Both pytest and gunittest are supported; follow the core `AGENTS.md` "Writing
Tests" for how to write either. Build or install the addon first (see above);
tests run a tool by name, so it must be on `PATH`.

**pytest** (preferred for new tests, as in core) goes in a `tests/`
directory next to the tool, named `<tool>_test.py` or `test_<tool>.py`. Use
synthetic data and `grass.tools`. CI runs the pytest suites; test collection
and configuration (markers, timeouts) are defined in the top-level
`pyproject.toml`. Run a tool's tests with:

```bash
export PYTHONPATH="$(grass --config python_path):${PYTHONPATH}"
export LD_LIBRARY_PATH="$(grass --config path)/lib:${LD_LIBRARY_PATH}"
pytest src/raster/r.example/tests/
```

Non-standard Python dependencies go in a `requirements.txt` next to the tool.

**gunittest** goes in a `testsuite/` directory and is the only option when
the test needs the `nc_spm` sample dataset. CI runs the full gunittest suite
against `nc_spm` (`.github/workflows/test.sh`, which calls
`python3 -m grass.gunittest.main ... --min-success`). To run one suite,
install the addon (the *g.extension* command above), start a GRASS session,
and run it as described in the core `AGENTS.md`. This repository's
[`UNIT_TESTS.md`](doc/development/submitting/UNIT_TESTS.md) is outdated.

## Linting, documentation, and commits

- Lint gate, same command as core: `pre-commit run --all-files`.
- Each addon needs `<name>.md` documentation with a synced `<name>.html`;
  follow the core documentation rules.
- Commit messages start with the tool name: `r.example: Add slope option`.
  Changes outside a single tool use the area as the prefix (e.g., `CI:`,
  `doc:`, `tests:`). The rest of the core commit message rules apply.
  Submit a new tool together with its tests and documentation in one pull
  request.
