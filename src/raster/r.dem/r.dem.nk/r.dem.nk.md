## DESCRIPTION

**r.dem.nk** - Implements the Nuth and Kääb (2011) algorithm for co-registering
two Digital Elevation Models (DEMs). The algorithm estimates and corrects for
vertical and horizontal offsets between the DEMs by minimizing elevation.

### MODEL

For stable terrain pixels:

$$
dh = SfM - LiDAR \approx \\
\Delta x \cdot \tan(\text{slope}) \cdot \cos(\text{aspect}) \\
+ \Delta y \cdot \tan(\text{slope}) \cdot \sin(\text{aspect}) \\
+ \Delta z
$$

Where $\Delta x$ (east), $\Delta y$ (north), $\Delta z$ (vertical) are solved by
ordinary least squares using raster-wide sums computed internally.

### HORIZONTAL APPLICATION (native)

Apply $\Delta z$ directly via raster algebra, and apply
$\left(\Delta x, \Delta y\right)$ as a sub-cell translation by temporarily
shifting the computational region by ($-\Delta x$, $-\Delta y$) and
resampling with `r.resamp.interp`, then resampling back to the LiDAR grid.

### ROBUSTNESS

Optional iterative sigma-clipping on residuals to reduce outlier influence.

The module always writes a residual raster named `output_resid` which contains
`output - lidar` on the stable-terrain mask used for regression.
When **-k** is provided, additional intermediate rasters are written:
`output_slope`, `output_aspect`, and `output_mask`.

## EXAMPLES

```bash
r.dem.nk sfm=sfm_dsm lidar=lidar_dsm stable_mask=stable
              output=sfm_coreg interp=bilinear iters=2 sigma=2.5
```

## REFERENCES

+ Nuth, C., and A. Kääb. 2011. “Co-Registration and Bias Corrections of
Satellite Elevation Data Sets for Quantifying Glacier Thickness Change.
”The Cryosphere 5 (1): 271–90. <https://doi.org/10.5194/tc-5-271-2011>.

## SEE ALSO

*[r.dem.icp](r.dem.icp.md)*

## AUTHORS

Corey T. White [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)
