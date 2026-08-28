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
- `full`: raw metadata object for current dataset
- `resolved`: fully materialized metadata object; inherited values are applied
  and schema form-value fields (`value`/`form`/`source`) are replaced by their
  values for programmatic consumers
- `extended`: selected `extended_metadata` only
  (all, branch, key path, or multiple selectors; resolved through lineage
  inheritance for derived datasets)
- `bands`: list source bands (optionally filtered by wavelength range)
- `history`: recursive aggregated lineage history, ordered by timestamp
  (uses `input_datasets_metadata` snapshots when referenced inputs are
  unavailable in current LOCATION)
- `validate`: metadata and lineage consistency checks
- `copy`: initialize or replace metadata from another hyperspectral cube;
  with existing target metadata, `--overwrite` is required and this map's last
  local processing step is preserved; the copy action itself is added to
  history
- `derive`: create metadata for an output map from `source_map`; assigns a new
  dataset ID, marks the output derived, stores one local source-to-output
  history entry from `command=`, applies generic overrides, and saves once;
  replacing existing target metadata requires `--overwrite`
- `merge-overrides`: apply top-level metadata overrides
  (e.g. `radiometric_quantity`) and deep-merge `extended_metadata` from the
  `overrides=` JSON into an existing map, saving in-place
- `add-history`: append a `processing_history` entry to an existing map;
  uses `source_map=` as input and `command=` as the command string

Output format (`format`) is global for all operations except `kv`, which is
available only with `operation=resolved`:

- `json` (default)
- `text`
- `csv`
- `kv`: line-oriented dotted key/value paths for `operation=resolved`; scalar
  strings escape backslashes, newlines, carriage returns, and equals signs,
  while numeric arrays are comma-separated

For `full` and `history`, `resolve_names=yes` resolves `inputs/outputs`
map names from current maps by `dataset_id` (display only; stored command
is unchanged).

For `operation=extended`, option `extended_select=` supports:

- `all` (default): full `extended_metadata`
- one branch (e.g., `acquisition`)
- one key path (e.g., `geometry.sun_zenith_deg`)
- multiple selectors at once (comma-separated), e.g.,
  `acquisition,geometry.sun_zenith_deg,processing`
- selectors with `extended_metadata.` prefix are also accepted
  (for example, `extended_metadata.geometry.sun_zenith_deg`)

Selectors are evaluated on resolved `extended_metadata` (current dataset
overrides plus inherited values from lineage).

Dataset provenance is stored in top-level key `derived`:

- `derived=false`: original imported dataset
- `derived=true`: any dataset created from other dataset(s)

### API (CLI)

Main options:

- `map=`: input `raster_3d` map
- `operation=`: `summary|full|resolved|extended|bands|history|validate|copy|derive|merge-overrides|add-history`
- `source_map=`: source `raster_3d` map for `operation=copy`,
  `operation=derive`, and `operation=add-history`
- `format=`: `json|text|csv|kv`
- `resolve_names=`: `yes|no` (for `full` and `history`)
- `wavelength_range=`: for `operation=bands` (example: `400-700`)
- `extended_select=`: for `operation=extended` (all/branch/path/multiple)
- `overrides=`: JSON string of metadata overrides for `operation=derive` or
  `operation=merge-overrides`; may contain top-level keys like
  `radiometric_quantity` and an `extended_metadata` key whose value is
  merged into the derived dataset's extended metadata
- `overrides_file=`: JSON overrides file for `operation=derive`; use `-` to
  read JSON from standard input; mutually exclusive with `overrides=`
- `command=`: command line string to store in processing history for
  `operation=derive` or `operation=add-history`

API examples:

::: code

    # Full metadata as JSON
    i.hyper.metadata map=my_cube operation=full format=json

    # Resolved metadata for downstream modules
    i.hyper.metadata map=my_cube operation=resolved format=json

    # Resolved metadata for command-line consumers
    i.hyper.metadata map=my_cube operation=resolved format=kv

    # Bands as CSV in 700-900 nm
    i.hyper.metadata map=my_cube operation=bands wavelength_range=700-900 format=csv

    # One extended branch
    i.hyper.metadata map=my_cube operation=extended extended_select=geometry

    # Multiple extended selectors
    i.hyper.metadata map=my_cube operation=extended \
      extended_select=acquisition,geometry.sun_zenith_deg,atmosphere.aod_550

    # Initialize metadata on a target cube from another hypercube
    i.hyper.metadata map=my_output_cube operation=copy source_map=my_source_cube

    # Replace existing target metadata and preserve the target's last local step
    i.hyper.metadata map=my_output_cube operation=copy source_map=my_source_cube --overwrite

    # Derive output metadata with generic overrides
    i.hyper.metadata map=my_output_cube operation=derive \
      source_map=my_input_cube command="my.module input=my_input_cube output=my_output_cube" \
      overrides_file=metadata-overrides.json

    # Append processing history entry
    i.hyper.metadata map=my_output_cube operation=add-history \
      source_map=my_input_cube command="i.hyper.atcorr input=my_input_cube output=my_output_cube sza=35.2"
:::

### JSON metadata structure

Imported datasets store full dataset description at top level.
Derived datasets store mandatory provenance keys and only local overrides.

::: code
{
  "schema_version": "1.0",
  "dataset_id": "5bc6cb5c55b44993afeb78f2da5c8ccf",
  "derived": true,
  "processing_history": [
    {
      "command": "i.hyper.preproc input=enmap output=enmap_sg steps=sav_gol
      window_length=7 polyorder=3",
      "timestamp": "2026-03-25T12:41:05.281173",
      "inputs": [{"id": "7da4f3e02b8f4ef2bc2a06fb0fe4bb8d", "map_name": "enmap@PERMANENT"}],
      "outputs": [{"id": "5bc6cb5c55b44993afeb78f2da5c8ccf", "map_name": "enmap_sg@PERMANENT"}]
    }
  ],
  "input_datasets_metadata": {
    "7da4f3e02b8f4ef2bc2a06fb0fe4bb8d": {
      "...": "full parent metadata snapshot"
    }
  }
}
:::

Derived dataset required top-level keys:

- `schema_version`
- `dataset_id`
- `derived`
- `processing_history`

Optional local override keys in derived datasets:

- `data_type`
- `sensor`
- `wavelength_units`
- `radiometric_quantity`
- `radiometric_units`
- `region`
- `bands`
- `extended_metadata`
- `dimensionality_reduction` (written only for outputs where dimensionality
  reduction is applied)

Inheritance rule:

- if an optional key is missing in derived dataset, value is inherited through
  lineage
- for multiple direct inputs, value is inherited only when all direct inputs
  resolve to the same value
- `dimensionality_reduction` is not inherited; it is present only when DR is
  applied for the current output dataset

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

Dimensionality reduction metadata is stored in top-level
`dimensionality_reduction`, not in `extended_metadata.processing`.

For derived datasets, top-level `input_datasets_metadata` stores full metadata
snapshots for all input datasets recursively to origin, keyed by `dataset_id`.
Embedded snapshots exclude nested `input_datasets_metadata`.
`operation=history` uses these snapshots when referenced input metadata are
unavailable in the current LOCATION.

Unified branches store cross-product keys. Product-specific branches store
source product keys used to derive unified values (provenance).
The same value may appear in both locations by design.

Only unified geometry keys under `extended_metadata.geometry` are used.

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

Copy metadata from another hypercube while preserving the current cube's last
local processing step:

::: code

    i.hyper.metadata map=my_output_cube operation=copy source_map=my_source_cube
:::

Show ATCORR-ready metadata subset (geometry + atmosphere + timing):

::: code

    i.hyper.metadata map=my_hyper_cube operation=extended \
      extended_select=acquisition.start_time_utc,acquisition.day_of_year,geometry.sun_zenith_deg,geometry.sun_azimuth_deg,geometry.view_zenith_deg,geometry.view_azimuth_deg,geometry.relative_azimuth_deg,atmosphere.aod_550,atmosphere.h2o_g_cm2,atmosphere.ozone_du \
      format=json
:::

## SEE ALSO

*[i.hyper](i.hyper.md),
[i.hyper.import](i.hyper.import.md),
[i.hyper.preproc](i.hyper.preproc.md),
[i.hyper.explore](i.hyper.explore.md)*

## AUTHORS

GRASS Development Team
Alen Mangafić and Tomaž Žagar, Geodetic Institute of Slovenia
Anna Petrášová, NCSU GeoForAll Lab
