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
