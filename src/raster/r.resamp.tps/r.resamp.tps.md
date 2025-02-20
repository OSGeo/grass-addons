## DESCRIPTION

*r.resamp.tps* performs multivariate thin plate spline interpolation
with regularization. The **input** is a raster map to be resampled to a
higher resolution or where NULL cells need to be interpolated. Output is
a raster map. Optionally, several raster maps can be specified to be
used as covariables which will improve results in areas with few points.
Raster maps to be used as covariables need to be provided separately
matching the grid geometry of the **input** raster map with the
**icovars** option and matching the grid geometry of the **output**
raster map with the **ocovars** option. The module can be regarded as a
combination of a multiple regression and spline interpolation.

The **min** options specifies the minimum number of points to be used
for interpolation. *r.resamp.tps* always performs tiled local TPS
interpolation. Tile sizes are variable and dependent on the extents of
the **min** nearest neighbors when a new tile is generated.

The **smooth** option can be used to reduce the influence of the splines
and increase the influence of the covariables. Without covariables, the
resulting surface will be smoother. With covariables and a large
smooting value, the resulting surface will be mainly determined by the
multiple regression component.

The **overlap** option controls how much tiles are overlapping when the
**min** option is smaller than the numer of input points. Tiling
artefacts occur with low values for the **min** option and the
**overlap** option. Increasing both options will reduce tiling artefacts
but processing will take more time.

The module works best with evenly spaced points. In case of highly
unevenly spaced points, e.g. remote sensing data with gaps due to cloud
cover, the module will take a long time to finish. For data with large
gaps, it is recommended to use first a different interpolation method
and then optionally use *r.resamp.tps* with the **smooth** option to
identify outliers (difference between the output of *r.resamp.tps* and
the data interpolated with a different method).

When using covariables, outliers might be created if the values of the
covariables of the current output cell are far outside the observed
range of covariables, or if the linear regression component of the TPS
interpolation for the covariables does not provide a good solution. Two
methods are provided to avoid outliers caused by covariables. The first
method (*lmfilter*) will discard covariables if R squared is larger than
the value provided with the *lmfilter* option. The second method
(*epfilter*) will discard covariables if the current value of a
covariable is outside the observed range of covariables by a factor of
(*epfilter*). The *epfilter* option typically results in more
interpolations using the supplied covariables than the *lmfilter* option
when both are adjusted to reject the same outliers.

The **memory** option controls only how much memory should be used for
the covariables and the intermediate output. The data needed for TPS
interpolation are always completely loaded to memory.

## REFERENCES

  - Hutchinson MF, 1995, Interpolating mean rainfall using thin plate
    smoothing splines. International Journal of Geographical Information
    Systems, 9(4), pp. 385-403
  - Wahba G, 1990, Spline models for observational data. In CBMS-NSF
    Regional Conference Series in Applied Mathematics. Philadelpia:
    Society for Industrial and Applied Mathematics

## SEE ALSO

*[v.surf.tps](v.surf.tps.md),
[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html),
[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html),
[v.surf.idw](https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html)*

## AUTHOR

Markus Metz
