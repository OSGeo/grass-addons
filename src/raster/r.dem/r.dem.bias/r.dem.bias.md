## DESCRIPTION

*r.dem.bias* removes terrain-correlated systematic bias that remains in a DEM
of Difference (DoD) after rigid co-registration. Alignment tools such as
*r.dem.coregister*, *r.dem.nk*, and *r.dem.icp* remove translation and rotation,
but a residual elevation difference often still varies with terrain (for
example a positive canopy bump in forest, or error that scales with slope,
roughness, or point density). This tool models that residual and subtracts it.

Two methods are provided through the **method** option.

### method=regression

Fits a multivariable linear model of the DoD on z-scored terrain predictors
over stable terrain, then subtracts the fitted surface from the full DoD.

- The dependent variable is the DoD restricted to the **stable_mask** region.
- Each **predictors** raster is standardized to zero mean and unit variance.
  Strongly skewed predictors (Pearson second skewness coefficient
  `|3 * (mean - median) / stddev| > 0.75`) are log-transformed before
  standardization (positive values only).
- *r.regression.multi* estimates the intercept and per-predictor coefficients,
  and the fitted bias field `b0 + sum(b_i * z_i)` is subtracted from the DoD.

Predictor rasters are typically produced by *r.dem.stats* (slope, roughness,
landform diversity, local sigma) together with a reference-DEM uncertainty
surface.

### method=forest

Estimates a local trimmed-median bias field over a masked subset of cells
(classically a forest canopy bump) and subtracts it.

- Within the **mask** region the DoD is trimmed to its
  [**trim_low**, **trim_high**] percentile core to exclude outliers.
- A moving-window median of that core over a **window**-cell window gives the
  local bias field.
- Outside the mask the bias field is zero, so unmasked cells are unchanged.

## NOTES

The optional **bias_field** output stores the estimated correction surface that
was subtracted, which is useful for inspection and reporting.

The mask used by `method=forest` is applied through a temporary mask context and
is removed automatically; the user's existing mask and computational region are
left untouched. Intermediate rasters are removed on exit.

## EXAMPLES

Regression correction using terrain predictors over stable ground:

```sh
r.dem.stats input=dem output=roughness metric=roughness_std window=13
r.dem.stats input=dem output=slope metric=slope

r.dem.bias method=regression dod=dod_1m \
    predictors=roughness,slope,sigma_lidar \
    stable_mask=stable output=dod_corrected bias_field=dod_bias
```

Forest canopy bump removal:

```sh
r.dem.bias method=forest dod=dod_1m mask=forest \
    window=21 trim_low=2.5 trim_high=97.5 output=dod_corrected
```

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.coregister](r.dem.coregister.md)*,
*[r.dem.errprop](r.dem.errprop.md)*,
*[r.dem.stats](r.dem.stats.md)*,
*[r.neighbors](r.neighbors.md)*,
*[r.regression.multi](r.regression.multi.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
