## DESCRIPTION

*r.dem.errprop* propagates per-source vertical uncertainty into a DEM of
Difference (DoD) and derives change-significance products from the combined
uncertainty. It is the analytical core of a DoD workflow: it answers *how much
of the measured elevation change is real* rather than measurement noise.

Given a DoD raster and one or more uncertainty (1 sigma) rasters, the tool
combines the uncertainty sources in quadrature:

```text
sigma_DoD = sqrt(sigma_1^2 + sigma_2^2 + ... + sigma_n^2)
```

Cells where any source is NULL are left NULL, so the propagated uncertainty is
only defined where every contributing source is defined. Typical sources are a
vertical-accuracy raster for each input DEM (for example derived from
land-cover class), plus optional co-registration or interpolation error terms.

From the propagated **output_sigma** the tool can additionally produce:

- **output_lod**: a Level of Detection raster, `LoD = z(confidence) *
  sigma_DoD`, where `z` is the two-tailed normal critical value. Cells of the
  DoD whose magnitude exceeds the LoD are considered significant change.
- **output_tvalue**: the standardized change magnitude `|DoD| / sigma_DoD`.
- **output_pvalue**: a two-tailed p-value raster, using either a normal
  approximation (Abramowitz and Stegun 26.2.17, evaluated in *r.mapcalc*) or a
  Student-t distribution with **df** degrees of freedom.
- **output_class**: a categorical erosion/deposition significance map.
  Each cell is labelled by the highest confidence level (68/90/95/99%) at which
  the change exceeds the corresponding LoD, signed by the direction of change.

## NOTES

The categorical output uses signed integer classes:

| Class | Meaning            | Class | Meaning               |
|-------|--------------------|-------|-----------------------|
| -4    | Erosion >=99%      | 1     | Deposition >=68%      |
| -3    | Erosion >=95%      | 2     | Deposition >=90%      |
| -2    | Erosion >=90%      | 3     | Deposition >=95%      |
| -1    | Erosion >=68%      | 4     | Deposition >=99%      |
| 0     | Not significant    |       |                       |

Category labels and a diverging color table are written automatically.

The propagated uncertainty raster pairs naturally with *r.dem.change*, which
applies an LoD threshold and reports volumetric change. The **output_sigma**
raster can be supplied to *r.dem.lod* as a precomputed uncertainty surface.

The tool requires the Python *scipy* package.

## EXAMPLES

Propagate two land-cover-based uncertainty rasters into a DoD and produce a
95% Level of Detection plus the categorical significance map:

```sh
r.dem.errprop dod=dod_1m sigma=sigma_sfm,sigma_lidar \
    output_sigma=sigma_dod output_lod=lod_95 \
    output_class=dod_significance confidence=0.95
```

Add a two-tailed p-value raster using a Student-t distribution:

```sh
r.dem.errprop dod=dod_1m sigma=sigma_sfm,sigma_lidar \
    output_sigma=sigma_dod output_pvalue=dod_p \
    pmethod=student df=120
```

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.change](r.dem.change.md)*,
*[r.dem.lod](r.dem.lod.md)*,
*[r.dem.stats](r.dem.stats.md)*,
*[r.mapcalc](r.mapcalc.md)*,
*[r.univar](r.univar.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
