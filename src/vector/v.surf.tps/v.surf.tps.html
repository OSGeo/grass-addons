<h2>DESCRIPTION</h2>

<em>v.surf.tps</em> performs multivariate thin plate spline
interpolation with regularization. The <b>input</b> is a 2D
or 3D vector <em>points</em> map. Values to interpolate can be the z
values of 3D points or the values in a user-specified attribute column
in a 2D or 3D vector map. Output is a raster map. Optionally, several
raster maps can be specified to be used as covariables which will
improve results in areas with few points. The module can be regarded
as a combination of a multiple regression and spline interpolation.

<p>
The <b>min</b> options specifies the minimum number of points to be
used for interpolation. If the number of input points is smaller than
or equal to the minimum number of points, global TPS interpolation is
used. If the number of input points is larger than the minimum number
of points, tiled local TPS interpolation is used. Tile sizes are
variable and dependent on the extents of the <b>min</b> nearest
neighbors when a new tile is generated.

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
artefacts but processing will take more time. Values for the
<b>overlap</b> option must be between 0 and 1.

<p>
The module works best with evenly spaced sparse points. In case of
highly unevenly spaced points, e.g. remote sensing data with gaps due
to cloud cover, the <b>thin</b> option should be used in order to avoid
tiling artefacts, otherwise a high number of minimum points and a large
<b>overlap</b> value are required, slowing down the module.

<p>
The <b>memory</b> option controls only how much memory should be used
for the covariables and the intermediate output. The input points are
always completely loaded to memory.

<h2>EXAMPLES</h2>

The computational region setting for the following examples:

<div class="code"><pre>
g.region -p rast=elev_state_500m
</pre></div>

<h3>Basic interpolation</h3>
Interpolation of 30 year precipitation normals in the North Carlolina
sample dataset:

<div class="code"><pre>
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140
</pre></div>

<h3>Interpolation with a covariable</h3>

<div class="code"><pre>
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140 covars=elev_state_500m
</pre></div>

<h3>Interpolation with a covariable and smoothing</h3>

<div class="code"><pre>
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140 covars=elev_state_500m smooth=0.1
</pre></div>

<h3>Tiled interpolation with a covariable and smoothing</h3>

<div class="code"><pre>
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=20 covars=elev_state_500m smooth=0.1 \
           overlap=0.1
</pre></div>

<!--
r.colors map=precip_30ynormals_3d rules=- <<EOF
950 red
1000 orange
1200 yellow
1400 cyan
1600 aqua
1800 blue
2500 violet
EOF
m.nviz.image elevation_map=elev_state_500m -a \
    mode=fine resolution_fine=1 color_map=precip_30ynormals_3d \
    position=0.59,0.74 height=40959 perspective=20 twist=0 \
    zexag=10 focus=105434,77092,1073 \
    light_position=0.68,-0.68,0.80 light_brightness=80 \
    output=v_surf_tps.tif format=tif size=798,585
d.legend -b raster=precip_30ynormals_3d label_step=300 \
    title="Annual Precipitation in Western North Carolina"
mogrify -trim -resize 600x -format png v_surf_tps.tif
optipng -o5 v_surf_tps.png
-->

<center>
    <img src="v_surf_tps.png">
    <p><em>
        Precipitation computed based on annual normals and
        elevation as a covariable
    </em></p>
</center>

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
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html">v.surf.rst</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.rst</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html">v.surf.idw</a>
</em>

<h2>AUTHOR</h2>

Markus Metz
