<h2>DESCRIPTION</h2>

<em>r.resamp.tps</em> performs multivariate thin plate spline
interpolation with regularization. The <b>input</b> is a raster
map to be resampled to a higher resolution or where NULL cells need to
be interpolated. Output is a raster map. Optionally, several
raster maps can be specified to be used as covariables which will
improve results in areas with few points. Raster maps to be used as
covariables need to be provided separately matching the grid geometry
of the <b>input</b> raster map with the <b>icovars</b> option and
matching the grid geometry of the <b>output</b> raster map with the
<b>ocovars</b> option. The module can be regarded as a combination of
a multiple regression and spline interpolation.

<p>
The <b>min</b> options specifies the minimum number of points to be
used for interpolation. <em>r.resamp.tps</em> always performs tiled
local TPS interpolation. Tile sizes are variable and dependent on the
extents of the <b>min</b> nearest neighbors when a new tile is generated.

<p>
The <b>smooth</b> option can be used to reduce the influence of the
splines and increase the influence of the covariables. Without
covariables, the resulting surface will be smoother. With covariables
and a large smooting value, the resulting surface will be mainly
determined by the multiple regression component.

<p>
The <b>overlap</b> option controls how much tiles are overlapping when
the <b>min</b> option is smaller than the numer of input points.
Tiling artefacts occur with low values for the <b>min</b> option and the
<b>overlap</b> option. Increasing both options will reduce tiling
artefacts but processing will take more time.

<p>
The module works best with evenly spaced points. In case of
highly unevenly spaced points, e.g. remote sensing data with gaps due
to cloud cover, the module will take a long time to finish. For data
with large gaps, it is recommended to use first a different
interpolation method and then optionally use <em>r.resamp.tps</em> with
the <b>smooth</b> option to identify outliers (difference between the
output of <em>r.resamp.tps</em> and the data interpolated with a
different method).

<p>
When using covariables, outliers might be created if the values of the
covariables of the current output cell are far outside the observed
range of covariables, or if the linear regression component of the TPS
interpolation for the covariables does not provide a good solution. Two
methods are provided to avoid outliers caused by covariables. The first
method (<em>lmfilter</em>) will discard covariables if R squared is
larger than the value provided with the <em>lmfilter</em> option. The
second method (<em>epfilter</em>) will discard covariables if the
current value of a covariable is outside the observed range of
covariables by a factor of (<em>epfilter</em>). The <em>epfilter</em>
option typically results in more interpolations using the supplied
covariables than the <em>lmfilter</em> option when both are adjusted to
reject the same outliers.

<p>
The <b>memory</b> option controls only how much memory should be used
for the covariables and the intermediate output. The data needed for
TPS interpolation are always completely loaded to memory.


<h2>REFERENCES</h2>

<ul>
  <li>Hutchinson MF, 1995, Interpolating mean rainfall using thin plate
    smoothing splines. International Journal of Geographical Information
    Systems, 9(4), pp. 385-403</li>
  <li>Wahba G, 1990, Spline models for observational data. In CBMS-NSF
    Regional Conference Series in Applied Mathematics. Philadelpia:
    Society for Industrial and Applied Mathematics</li>
</ul>

<h2>SEE ALSO</h2>

<em>
<a href="v.surf.tps.html">v.surf.tps</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html">v.surf.rst</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.bspline</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html">v.surf.idw</a>
</em>

<h2>AUTHOR</h2>

Markus Metz
