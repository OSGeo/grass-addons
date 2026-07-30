## DESCRIPTION

*r.dem.stats* computes terrain surface metrics from a DEM (or a DEM of
Difference). The outputs are the predictor rasters used to model
terrain-correlated DoD uncertainty and systematic bias, for example as inputs
to *r.dem.bias* or as an uncertainty source for *r.dem.errprop*.

A single metric is selected per run through the **metric** option:

- **slope**: surface slope from *r.slope.aspect*, in degrees or radians as
  selected with **slope_format** (default degrees).
- **roughness_std**: local roughness as the Gaussian-weighted focal
  standard deviation of elevation (*r.neighbors*).
- **diversity_geomorphon**: landform category richness in a moving
  window, computed from *r.geomorphon* forms.
- **diversity_shannon**: local Shannon diversity
  `H' = -sum(p * log(p))` over category proportions in a window, computed from
  a categorical input such as a geomorphon forms map. The logarithm base is
  selected with **log_base** (`e`, `2`, or `10`; default `e`). With the
  **-e** flag the matching Shannon evenness `J = H' / log(S)` is also written
  as `<output>_evenness`.
- **error_sigma_local**: a robust local standard deviation via the median
  absolute deviation, `sigma = 1.4826 * median(|x - median(x)|)` in a moving
  window. Use a DoD raster as **input** to obtain a spatially varying DoD
  uncertainty surface.

## NOTES

The **window** must be an odd integer of at least 3 cells. Focal metrics use a
Gaussian weighting whose falloff is derived from the window radius, matching the
focal behaviour used throughout the DoD workflow.

For **diversity_shannon** the input is expected to be categorical (integer
classes). A natural pairing is to first compute a geomorphon forms map and then
run *r.dem.stats* with `metric=diversity_shannon` on that map.

Intermediate rasters are removed on exit. The tool honours the current
computational region and the `--overwrite` flag.

## EXAMPLES

Local roughness over a 13-cell window:

```sh
r.dem.stats input=dem output=dem_roughness metric=roughness_std window=13
```

Spatially varying DoD uncertainty from a difference raster:

```sh
r.dem.stats input=dod output=sigma_local metric=error_sigma_local window=21
```

Shannon diversity with evenness from a geomorphon forms map:

```sh
r.geomorphon elevation=dem forms=dem_forms search=7 flat=4
r.dem.stats input=dem_forms output=dem_shannon \
    metric=diversity_shannon window=15 -e
```

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.bias](r.dem.bias.md)*,
*[r.dem.errprop](r.dem.errprop.md)*,
*[r.geomorphon](r.geomorphon.md)*,
*[r.neighbors](r.neighbors.md)*,
*[r.slope.aspect](r.slope.aspect.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
