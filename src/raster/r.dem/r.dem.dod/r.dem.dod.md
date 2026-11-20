## DESCRIPTION

*r.dem.dod* computes a DEM of Difference (DoD), `output = dem - reference`,
on the current computational region. Negative values are surface lowering
(erosion) and positive values are surface raising (deposition). The output is
the DoD that *r.dem.bias*, *r.dem.lod*, *r.dem.change*, *r.dem.errprop*, and
*r.dem.screen* take through their **dod** option.

Inputs that are not aligned with the computational region, either because
their resolution differs or because their cell edges are offset from the
region grid, are resampled onto the region with *r.resamp.interp* before
differencing. The **interp** option selects `bilinear` (default) or
`bicubic` interpolation. A warning reports the resolution and origin offset
of every resampled input. Inputs already on the region grid, such as the
output of *r.dem.nk*, are differenced directly.

The output carries the r.dem DoD color palette: erosion runs yellow to orange
to red to magenta as it deepens, near-zero differences are pale green, and
deposition runs cyan to teal to blue to navy. The palette breaks sit at 0.1,
0.3, 0.6, and 1.0 times a saturation value R on either side of zero. **range**
sets R. Without it, R is the 98th percentile of `|DoD|` rounded up to one
significant digit. Differences beyond R keep the end colors.

The output metadata records the command, both source maps, the interpolation
method, and R. Units are copied from **dem**. When both inputs have
timestamps, the output receives the interval from the start of the
**reference** timestamp to the end of the **dem** timestamp, so it can be
registered in a space-time raster dataset with *t.register*.

## NOTES

Differencing respects the computational region and the raster mask. Cells
that are null in either input are null in the output.

When an input is finer than the computational region, interpolation samples
it without aggregating the cells in between. Aggregate it first with a method
like *r.resamp.stats* `method=average` if that matters for the analysis.

To compare multiple DoDs, for example before and after co-registration,
pass the same **range** so the maps share one color scale.

## EXAMPLES

Difference a co-registered post-event DEM against the reference lidar DEM:

```sh
g.region raster=elev_lid792_1m
r.dem.dod dem=dsm_post_nk reference=elev_lid792_1m output=dod
```

Two DoDs on a shared color scale, before and after co-registration:

```sh
r.dem.dod dem=dsm_post reference=elev_lid792_1m output=dod_raw range=1
r.dem.dod dem=dsm_post_nk reference=elev_lid792_1m output=dod_nk range=1
```

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.bias](r.dem.bias.md)*,
*[r.dem.change](r.dem.change.md)*,
*[r.dem.lod](r.dem.lod.md)*,
*[r.dem.nk](r.dem.nk.md)*,
*[r.resamp.interp](r.resamp.interp.md)*,
*[r.resamp.stats](r.resamp.stats.md)*,
*[t.register](t.register.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
