## DESCRIPTION

*t.strds.copy* copies a space time raster dataset (STRDS) together with all of
its registered raster maps from a source mapset into the **current** mapset,
preserving the temporal type and the start/end timestamps of every map.

GRASS keeps raster data and the temporal database separate and per-mapset, so
duplicating an STRDS requires copying the raster maps with *g.copy*, recreating
the STRDS with *t.create*, and re-registering the maps with *t.register*. This
module performs all three steps in one call.

## NOTES

The **output** STRDS is always created in the current mapset; you cannot write
into another mapset. The **input** should be given fully qualified as
`name@mapset` when the source lives in a different mapset, and that mapset must
be in the search path (see *g.mapsets*).

The new STRDS inherits the title and description of the source STRDS.

## EXAMPLES

Copy an STRDS from another mapset into the current one:

```sh
t.strds.copy input=S2_ndvi@source_mapset output=S2_ndvi
```

Copy an STRDS, overwriting an existing output of the same name:

```sh
t.strds.copy input=S2_ndvi@source_mapset output=S2_ndvi_copy --overwrite
```

## SEE ALSO

*[t.create](t.create.md),
[t.register](t.register.md),
[t.rast.list](t.rast.list.md)*

## AUTHOR

[Paulo van Breugel](https://ecodiv.earth),
[HAS green academy](https://has.nl),
[Innovative Biomonitoring research group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/),
[Climate-robust Landscapes research group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
