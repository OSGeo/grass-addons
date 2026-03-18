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

- `view`: human-readable metadata summary
- `json`: metadata as JSON
- `bands`: list spectral bands (optionally filtered by wavelength range)
- `history`: print processing history
- `validate`: check metadata consistency

### JSON metadata structure

Dataset-level fields are stored in `dataset` in `hyper.json`.

::: code
{
  "schema_version": "1.0",
  "dataset": {
    "sensor": "EnMAP",
    "wavelength_units": "nm",
    "radiometric_quantity": "surface_reflectance",
    "radiometric_units": "unitless",
    "acquisition_datetime": "2024-06-20T10:18:39.026423Z",
    "solar_zenith_angle": 24.475721,
    "solar_azimuth_angle": 156.193067,
    "satellite_zenith_angle": 21.917226,
    "satellite_azimuth_angle": 14.116742
  },
  "bands": { ... },
  "components": { ... },
  "processing_history": [ ... ],
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

    i.hyper.metadata map=my_hyper_cube operation=view
:::

Show bands in visible range:

::: code

    i.hyper.metadata map=my_hyper_cube operation=bands wavelength_range=400-700
:::

## SEE ALSO

*[i.hyper](i.hyper.html),
[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html)*

## AUTHORS

GRASS Development Team
