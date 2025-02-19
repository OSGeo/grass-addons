<h2>DESCRIPTION</h2>

This module extracts selected categories from an integer raster map
into a new raster, similarly to
<em><a href="https://grass.osgeo.org/grass-stable/manuals/v.extract.html">v.extract</a></em>
for vectors. The categories and color table are preserved.

<p>
The category values can be specified as:

<ul>
<li>cat1,cat2,...</li>
<li>cat1-cat3</li>
<li>cat1-</li>
<li>-cat1</li>
<li>and their combination: -cat1,cat2,cat3-cat6</li>
</ul>

<p>
The extent of the new raster can be changed with flag <b>-c</b>
to fit the extent of the extracted data. When using flag <b>-s</b>
output raster is a reclassified input raster
(see <em><a href="https://grass.osgeo.org/grass-stable/manuals/r.reclass.html">r.reclass</a></em>
for details).


<h2>NOTES</h2>
This implementation supports only integer raster maps (type CELL).

<h2>EXAMPLES</h2>

The following examples are using the full North Carolina sample
dataset. We will extract certain zipcodes.


First print zipcodes raster info:
<div class="code"><pre>
g.region raster=zipcodes -p
r.info zipcodes -rg
</pre></div>
<pre>
...
rows=1350
cols=1500
min=27511
max=27610
...
</pre>

Now we extract 2 categories and automatically adjust the raster extent
to fit the extracted data.

<div class="code"><pre>
r.extract input=zipcodes output=selected_zipcodes cats=27605,27601 -c
r.info selected_zipcodes -rg
</pre></div>
<pre>
...
rows=404
cols=377
min=27601
max=27605
...
</pre>



<h2>SEE ALSO</h2>

<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.reclass.html">r.reclass</a></em> (used in this implementation)<br>
<em><a href="https://grass.osgeo.org/grass-stable/manuals/v.extract.html">v.extract</a></em> (for extracting vector data)


<h2>AUTHOR</h2>

Anna Petrasova, <a href="https://geospatial.ncsu.edu/geoforall/">NCSU GeoForAll Lab</a>
