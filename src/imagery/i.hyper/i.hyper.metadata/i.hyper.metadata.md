---
name: i.hyper.metadata
description: View and manage hyperspectral metadata for 3D raster maps
---

## DESCRIPTION

*i.hyper.metadata* reads and manages metadata for hyperspectral 3D raster maps
created by the *i.hyper* toolchain.

Metadata is loaded from `hyper.json` when present and falls back to legacy
`r3.support` description parsing for backward compatibility.

## NOTES

Supported operations:

- `view`: human-readable metadata summary
- `json`: metadata as JSON
- `bands`: list spectral bands (optionally filtered by wavelength range)
- `history`: print processing history
- `validate`: check metadata consistency
- `upgrade`: convert legacy metadata to JSON

## EXAMPLES

View metadata summary:

::: code

    i.hyper.metadata map=my_hyper_cube operation=view
:::

Show bands in visible range:

::: code

    i.hyper.metadata map=my_hyper_cube operation=bands wavelength_range=400-700
:::

Upgrade legacy map metadata to JSON:

::: code

    i.hyper.metadata map=my_hyper_cube operation=upgrade
:::

## SEE ALSO

*[i.hyper](i.hyper.html),
[i.hyper.import](i.hyper.import.html),
[i.hyper.preproc](i.hyper.preproc.html),
[i.hyper.explore](i.hyper.explore.html),
[r3.info](https://grass.osgeo.org/grass-stable/manuals/r3.info.html),
[r3.support](https://grass.osgeo.org/grass-stable/manuals/r3.support.html)*

## AUTHORS

GRASS Development Team
