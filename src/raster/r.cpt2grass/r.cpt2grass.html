<h2>DESCRIPTION</h2>

Module <em>r.cpt2grass</em> converts
<a href="http://gmt.soest.hawaii.edu/">GMT</a> color palette
(*.cpt) format
to GRASS color table format and assigns it to a given raster map.

Input can be either cpt file given in <b>input</b> option or
a URL of the cpt file specified in <b>url</b> option.
Specifying URL is particularly useful when using color tables
from <a href="http://soliton.vm.bytemark.co.uk/pub/cpt-city/">cpt-city</a>,
because many color tables can be quickly tested without
downloading the files.

When option <b>map</b> is specified <em>r.cpt2grass</em>
assigns the color rules to the given raster map.
Depending on the values of the original cpt file,
it may be advantageous to use the <b>-s</b> to stretch the
colors based on the range of values of the map.





<h2>NOTES</h2>
RGB and HSV models are supported.
The expected format of the cpt file is:
<pre>
# COLOR_MODEL = RGB
value1 R G B value2 R G B
value2 R G B value3 R G B
...
</pre>
Named colors are not supported.

<h2>EXAMPLES</h2>

From <a href="http://soliton.vm.bytemark.co.uk/pub/cpt-city/">cpt-city</a>
we download a
<a href="http://soliton.vm.bytemark.co.uk/pub/cpt-city/jjg/misc/rainfall.cpt">rainfall</a>
color table and convert it to GRASS color table.
If we don't specify output file, it is printed to standard output:

<div class="code"><pre>
r.cpt2grass input=rainfall.cpt
</pre></div>
<pre>
0.000 229:180:44
20.000 229:180:44
20.000 242:180:100
40.000 242:180:100
40.000 243:233:119
60.000 243:233:119
60.000 145:206:126
80.000 145:206:126
80.000 67:190:135
100.000 67:190:135
100.000 52:180:133
120.000 52:180:133
120.000 6:155:66
140.000 6:155:66
</pre>

We set two different elevation color tables - continuous and discrete gradients.
We have to stretch the color tables to fit the raster map range:

<div class="code"><pre>
r.cpt2grass url=http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_screen.cpt map=elevation -s
r.cpt2grass url=http://soliton.vm.bytemark.co.uk/pub/cpt-city/cb/seq/YlOrBr_09.cpt map=elevation -s
</pre></div>

We can display legend:
<div class="code"><pre>
d.legend raster=elevation labelnum=10 at=5,50,7,10
</pre></div>

<center>
<img src="r_cpt2grass_color_table_DEM_screen.png" alt="DEM color table">
<img src="r_cpt2grass_color_table_YlOrBr_09.png" alt="yellow to brown color table">
</center>

<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/r.colors.html">r.colors</a>
</em>

<h2>AUTHORS</h2>

Anna Petrasova, <a href="http://gis.ncsu.edu/osgeorel/">NCSU OSGeoREL</a><br>
Hamish Bowman (original Bash script)
