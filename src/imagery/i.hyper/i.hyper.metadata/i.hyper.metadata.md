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
- `bands`: list source bands (optionally filtered by wavelength range)
- `history`: recursive aggregated lineage history, ordered by timestamp
- `validate`: metadata and lineage consistency checks

Output format (`format`) is global for all operations:

- `json` (default)
- `text`
- `csv`

For `full` and `history`, `resolve_names=yes` resolves `inputs/outputs` map names
from current maps by `dataset_id` (display only; stored command is unchanged).

### JSON metadata structure

Dataset-level fields are stored at the top level in `hyper.json`.

::: code
{
  "schema_version": "1.0",
  "dataset_id": "7da4f3e02b8f4ef2bc2a06fb0fe4bb8d",
  "data_type": "spectral",
  "sensor": "EnMAP",
  "wavelength_units": "nm",
  "radiometric_quantity": "surface_reflectance",
  "radiometric_units": "unitless",
  "acquisition_datetime": "2024-06-20T10:18:39.026423Z",
  "solar_zenith_angle": 24.475721,
  "solar_azimuth_angle": 156.193067,
  "satellite_zenith_angle": 21.917226,
  "satellite_azimuth_angle": 14.116742,
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
  "custom": { ... }
}
:::

### EnMAP mapping used for dataset fields

When metadata is produced by `i.hyper.import product=enmap`, values are mapped from EnMAP `*-METADATA.XML` as:

- `Date of acquisition` <- `datatakeStart` (fallback `temporalCoverage/startTime`)
- `Solar zenith angle` <- `90 - sunElevationAngle/center`
- `Solar azimuth angle` <- `sunAzimuthAngle/center`
- `Satellite azimuth angle` <- `sceneAzimuthAngle/center`
- `Satellite zenith angle` <- direct zenith tag if present, otherwise derived from `acrossOffNadirAngle/center` + `alongOffNadirAngle/center`

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

## SEE ALSO

*[i.hyper](i.hyper.html),
[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html)*

## AUTHORS

GRASS Development Team
