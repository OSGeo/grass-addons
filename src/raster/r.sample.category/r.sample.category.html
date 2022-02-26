<h2>DESCRIPTION</h2>

<p>
<em>r.sample.category</em> generates points at random locations.
Each category (class) in a raster map will contain specified number
of random points.

<p>Different number of points can be specified for different categories.
For example, if there are categories 1, 4, 7 in the input raster map,
and npoints=100,200,300, 100 points will be generated in category 1,
200 points in category 4 and 300 points in category 7.
If only one number is specified, it will be used for every category.

<h2>NOTES</h2>

Mask (<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.mask.html">r.mask</a></em>) to create points in areas
with each category, thus mask cannot be active when the module is used.

<p>Categories are identified based on current computational region.

<h2>EXAMPLE</h2>

<h3>Generate random points</h3>

Generate three points at random location for each category (class)
in the raster map:

<div class="code"><pre>
g.region raster=landclass96
r.sample.category input=landclass96 output=landclass_points npoints=3
</pre></div>

Show the result:

<div class="code"><pre>
d.rast map=landclass96
d.vect map=landclass_points icon=basic/circle fill_color=aqua color=blue size=10
</pre></div>

<!--
export GRASS_RENDER_IMMEDIATE=cairo
export GRASS_RENDER_FILE=r.sample.category.png
export GRASS_RENDER_WIDTH=800
export GRASS_RENDER_HEIGHT=800
export GRASS_RENDER_FILE_READ=TRUE
d.rast map=landclass96
d.vect map=landclass_points icon=basic/circle fill_color=aqua color=blue size=10
mogrify -trim r.sample.category.png
optipng -o9 r.sample.category.png
-->

<p>
<center>
<img src="r.sample.category.png"><br>
Figure: Three random points in each category of landclass raster map
</center>

<h3>Create a table with values sampled from rasters</h3>

Create 2 random points per each category (class) in landclass96 raster
and sample elevation and geology_30m rasters at these points:

<div class="code"><pre>
r.sample.category input=landclass96 output=landclass_points sampled=elevation,geology_30m npoints=2
</pre></div>

Look at the created data:

<div class="code"><pre>
v.db.select landclass_points sep=comma
</pre></div>

The result of <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.db.select.html">v.db.select</a></em>
is CSV table which can be used, for example in a spreadsheet application:

<div class="code"><pre>
cat,landclass96,elevation,geology_30m
1,1,102.7855,270
2,1,105.78,270
3,2,114.5954,217
4,2,137.4816,921
5,3,71.19167,270
6,3,93.33904,270
7,4,76.41077,262
8,4,97.54424,217
9,5,138.455,405
10,5,88.8075,270
11,6,126.5298,217
12,6,86.73177,217
13,7,134.5381,217
14,7,99.6844,270
</pre></div>


<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/v.sample.html">v.sample</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.random.html">r.random</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.random.cells.html">r.random.cells</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.random.html">v.random</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.what.rast.html">v.what.rast</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.describe.html">r.describe</a>
</em>


<h2>AUTHORS</h2>

Vaclav Petras, <a href="http://gis.ncsu.edu/osgeorel/">NCSU OSGeoREL</a>,<br>
Anna Petrasova, <a href="http://gis.ncsu.edu/osgeorel/">NCSU OSGeoREL</a>
