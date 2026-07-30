## DESCRIPTION

*r.dem.nk* implements the Nuth and Kääb (2011) algorithm for co-registering
two Digital Elevation Models (DEMs). The algorithm estimates and corrects for
vertical and horizontal offsets between the DEMs by minimizing elevation
differences on stable terrain.

### Model

For stable terrain pixels:

```text
dh = SfM - LiDAR
   approx. delta_x * tan(slope) * cos(aspect)
         + delta_y * tan(slope) * sin(aspect)
         + delta_z
```

Where `delta_x` (east), `delta_y` (north), `delta_z` (vertical) are solved by
ordinary least squares using raster-wide sums computed internally. Only
stable-terrain cells whose slope lies between **slope_min** and **slope_max**
(degrees; defaults 2 and 85) enter the regression, excluding near-flat and
near-vertical cells.

### Iterative solve

The linear model above is only first order, so a single pass under-estimates
shifts larger than one cell. The module therefore solves the increment on a
working surface, accumulates it into the running transform, re-warps the
working surface from the original SfM by the accumulated transform, and
repeats until the increment falls below **tol** (in map units) or **max_iter**
outer passes are reached. If the passes do not converge, a warning is issued
and the last estimate is used.

### Horizontal application (native)

The solved offsets are applied as a single inverse warp: each output cell at
map coordinate `(x, y)` samples the original SfM at
`(x + delta_x, y + delta_y)` (using **interp**) and subtracts `delta_z`.
No region shifting or external resampling tool is involved.

### Robustness

Optional iterative sigma-clipping on residuals (**iters** per outer pass)
reduces outlier influence during each solve.

The module always writes a residual raster named `output_resid` which contains
`output - lidar` on the stable-terrain mask used for regression.
When **-k** is provided, additional intermediate rasters are written:
`output_slope`, `output_aspect`, and `output_mask`.

### Saving and reusing a transform

**transform_output** writes the solved offsets (`dz`, `dx`, `dy`) to a small
text file. **apply_transform** reads such a file and applies it directly,
skipping the regression. This lets a transform solved on one surface (for
example a clean bare-earth DTM) be replayed onto another surface from the same
acquisition (for example its DSM) so both share the same horizontal alignment.
In apply mode the **stable_mask** is used only to define the reported residual
raster, so a near-flat mask no longer triggers the "not enough valid pixels"
error.

## EXAMPLES

Solve and save the transform:

```sh
r.dem.nk sfm=sfm_dsm lidar=lidar_dsm stable_mask=stable \
    output=sfm_coreg interp=bilinear iters=2 sigma=2.5 \
    transform_output=nk_transform.txt
```

Replay the saved transform onto another surface:

```sh
r.dem.nk sfm=sfm_dtm lidar=lidar_dtm stable_mask=stable \
    output=sfm_dtm_coreg apply_transform=nk_transform.txt
```

## REFERENCES

- Nuth, C., and A. Kääb. 2011. "Co-Registration and Bias Corrections of
  Satellite Elevation Data Sets for Quantifying Glacier Thickness Change."
  *The Cryosphere* 5 (1): 271-90. <https://doi.org/10.5194/tc-5-271-2011>

## SEE ALSO

*[r.dem](r.dem.md)*,
*[r.dem.coregister](r.dem.coregister.md)*,
*[r.dem.icp](r.dem.icp.md)*

## AUTHORS

Corey T. White, Center for Geospatial Analytics, NC State University
