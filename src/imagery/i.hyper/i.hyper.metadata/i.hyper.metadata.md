---
name: i.hyper.metadata
description: View and manage hyperspectral metadata for 3D raster maps
---

## DESCRIPTION

*i.hyper.metadata* reads and manages metadata for hyperspectral 3D raster maps
created by the *i.hyper* toolchain.

Metadata is loaded from `hyper.json`.

## NOTES

Supported operations:

- `summary`: concise metadata summary for current dataset
- `full`: full metadata object for current dataset
- `extended`: selected `extended_metadata` only (all, branch, key path, or multiple selectors)
- `bands`: list source bands (optionally filtered by wavelength range)
- `history`: recursive aggregated lineage history, ordered by timestamp (uses `input_datasets_metadata` snapshots when referenced inputs are unavailable in current LOCATION)
- `validate`: metadata and lineage consistency checks

Output format (`format`) is global for all operations:

- `json` (default)
- `text`
- `csv`

For `full` and `history`, `resolve_names=yes` resolves `inputs/outputs` map names
from current maps by `dataset_id` (display only; stored command is unchanged).

For `operation=extended`, option `extended_select=` supports:

- `all` (default): full `extended_metadata`
- one branch (e.g., `acquisition`)
- one key path (e.g., `geometry.sun_zenith_deg`)
- multiple selectors at once (comma-separated), e.g., `acquisition,geometry.sun_zenith_deg,processing`
- selectors with `extended_metadata.` prefix are also accepted
  (for example, `extended_metadata.geometry.sun_zenith_deg`)

Dataset provenance is stored in top-level key `derived`:

- `derived=false`: original imported dataset
- `derived=true`: any dataset created from other dataset(s)

### API (CLI)

Main options:

- `map=`: input `raster_3d` map
- `operation=`: `summary|full|extended|bands|history|validate`
- `format=`: `json|text|csv`
- `resolve_names=`: `yes|no` (for `full` and `history`)
- `wavelength_range=`: for `operation=bands` (example: `400-700`)
- `extended_select=`: for `operation=extended` (all/branch/path/multiple)

API examples:

::: code

    # Full metadata as JSON
    i.hyper.metadata map=my_cube operation=full format=json

    # Bands as CSV in 700-900 nm
    i.hyper.metadata map=my_cube operation=bands wavelength_range=700-900 format=csv

    # One extended branch
    i.hyper.metadata map=my_cube operation=extended extended_select=geometry

    # Multiple extended selectors
    i.hyper.metadata map=my_cube operation=extended \
      extended_select=acquisition,geometry.sun_zenith_deg,atmosphere.aod_550
:::

### JSON metadata structure

Core dataset fields are stored at the top level in `hyper.json`.
Additional product and correction metadata are stored in `extended_metadata`.

::: code
{
  "schema_version": "1.0",
  "dataset_id": "7da4f3e02b8f4ef2bc2a06fb0fe4bb8d",
  "derived": false,
  "data_type": "spectral",
  "sensor": "EnMAP",
  "wavelength_units": "nm",
  "radiometric_quantity": "surface_reflectance",
  "radiometric_units": "unitless",
  "acquisition_datetime": "2024-06-20T10:18:39.026423Z",
  "region": {
    "north": 2615535,
    "south": 2581725,
    "west": 4705605,
    "east": 4743495,
    "top": 2445.3,
    "bottom": 418.416
  },
  "bands": {
    "count": 250,
    "count_valid": 167,
    "wavelength": [ ... ],
    "fwhm": [ ... ],
    "validity": [true, true, false, ...]
  },
  "processing_history": [
    {
      "command": "i.hyper.import input=/data/... product=enmap output=enmap -n",
      "timestamp": "2026-03-18T11:25:39.596678",
      "inputs": [],
      "outputs": [{"id": "7da4f3e02b8f4ef2bc2a06fb0fe4bb8d", "map_name": "enmap@PERMANENT"}]
    }
  ],
  "input_datasets_metadata": {
    "43b042696578492095397fd343f43b47": { "...": "full parent metadata snapshot" }
  },
  "extended_metadata": {
    "acquisition": { "...": "..." },
    "geometry": { "...": "..." },
    "radiometry": { "...": "..." },
    "atmosphere": { "...": "..." },
    "quality": { "...": "..." },
    "processing": { "...": "..." },
    "uncertainty": { "...": "..." },
    "enmap": { "...": "product-native provenance keys" },
    "prisma": { "...": "product-native provenance keys" },
    "tanager": { "...": "product-native provenance keys" }
  }
}
:::

### Extended Metadata Branches

Common unified branches:

- `acquisition`
- `geometry`
- `radiometry`
- `atmosphere`
- `quality`
- `processing`
- `uncertainty`

Product-specific branches:

- `enmap`
- `prisma`
- `tanager`

For derived datasets, top-level `input_datasets_metadata` stores full metadata
snapshots for all input datasets recursively to origin, keyed by `dataset_id`.
Embedded snapshots exclude nested `input_datasets_metadata`.
`operation=history` uses these snapshots when referenced input metadata are
unavailable in the current LOCATION.

Unified branches store cross-product keys. Product-specific branches store
source product keys used to derive unified values (provenance).
The same value may appear in both locations by design.

Legacy compatibility:

- older imports may still use `extended_metadata.scene.geometry`

For key mapping and provenance rules, see:

- `extended_metadata_unification.md`

## EXAMPLES

View metadata summary:

::: code

    i.hyper.metadata map=my_hyper_cube operation=summary format=text
:::

Show bands in visible range:

::: code

    i.hyper.metadata map=my_hyper_cube operation=bands wavelength_range=400-700
:::

Show full recursive history with current map names:

::: code

    i.hyper.metadata map=my_hyper_cube operation=history resolve_names=yes
:::

Show all extended metadata:

::: code

    i.hyper.metadata map=my_hyper_cube operation=extended extended_select=all
:::

Show one specific extended metadata key:

::: code

    i.hyper.metadata map=my_hyper_cube operation=extended \
      extended_select=geometry.sun_zenith_deg
:::

Show selected branches and key paths at the same time:

::: code

    i.hyper.metadata map=my_hyper_cube operation=extended \
      extended_select=acquisition,geometry.sun_zenith_deg,processing
:::

## SEE ALSO

*[i.hyper](i.hyper.html),
[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html)*

## AUTHORS

GRASS Development Team
