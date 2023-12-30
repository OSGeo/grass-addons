<h2>DESCRIPTION</h2>

<em>d.explantion.plot</em> creates a plot of rasters and their relations
which can serve as an explanation of a raster operation performed by
a module or function.

<p>
Up to four rasters are supported. The default operators assume rasters to
have the following relation:

<p><em>
a + b -> c
</em></p>


<h2>EXAMPLES</h2>

<h3>Example using generated data</h3>

In Bash:

<div class="code"><pre>
g.region n=99 s=0 e=99 w=0 rows=3 cols=3
r.mapcalc expression="a = rand(0., 5)" seed=1
r.mapcalc expression="b = rand(0., 5)" seed=2
r.mapcalc expression="c = rand(0., 5)" seed=3
r.series input=a,b,c output=d method=average
</pre></div>

In Python:

<div class="code"><pre>
import grass.jupyter as gj
plot = gj.Map(use_region=True, width=700, height=700)
plot.d_background(color="white")
plot.run("d.explanation.plot", a="a", b="b", c="c", d="d", operator_font="FreeMono:Regular")
plot.show()
</pre></div>

<center>
<img src="d_explanation_plot_with_r_series.png">
<p><em>Figure: Resulting image for r.series</em></p>
</center>

<h3>Example using artificial data</h3>

<div class="code"><pre>
r.in.ascii input=- output=input_1 &lt;&lt;EOF
north: 103
south: 100
east: 103
west: 100
rows: 3
cols: 3
5 * 9
* 5 *
* 5 5
EOF
r.in.ascii input=- output=input_2 &lt;&lt;EOF
north: 103
south: 100
east: 103
west: 100
rows: 3
cols: 3
3 4 4
2 2 2
2 1 1
EOF
r.colors map=input_1,input_2 color=viridis
g.region raster=input_1
r.patch input=input_1,input_2 output=result
d.mon wx0 width=400 height=400 output=r_patch.png
d.explanation.plot a=input_1 b=input_2 c=result
</pre></div>

<center>
<img src="d_explanation_plot.png">
<p><em>Figure: Resulting image for r.patch</em></p>
</center>

<h2>KNOWN ISSUES</h2>

<ul>
    <li>
        Issue <a href="https://trac.osgeo.org/grass/ticket/3381">#3381</a>
        prevents d.rast.num to be used with <tt>d.mon cairo</tt>,
        so <tt>d.mon wx0</tt> needs to be used with this module.
        Using environmental variables for rendering directly or
        using tools such as <em>Map</em> from <em>grass.jupyter</em>
        avoids the issues.
    </li>
    <li>
        Issue <a href="https://trac.osgeo.org/grass/ticket/3382">#3382</a>
        prevents usage of centered text with <tt>d.mon wx0</tt>, so the
        hardcoded values for text does not work perfectly.
    </li>
    <li>
        Issue <a href="https://trac.osgeo.org/grass/ticket/3383">#3383</a>
        prevents d.rast.num to be saved to the image with
        <tt>d.mon wx0</tt>, taking screenshot is necessary
        (with a powerful screenshot tool, this also
        addresses the copping issue below).
    </li>
    <li>
        The size of the display must be square to have rasters and their
        cells as squares, e.g., <tt>d.mon wx0 width=400 height=400</tt>
        must be used. The image needs to be cropped afterwards,
        e.g. using ImageMagic's <tt>mogrify -trim image.png</tt>.
    </li>
</ul>


<h2>SEE ALSO</h2>

<em>
  <a href="https://grass.osgeo.org/grass-stable/manuals/g.region.html">g.region</a>,
  <a href="https://grass.osgeo.org/grass-stable/manuals/d.frame.html">d.frame</a>,
  <a href="https://grass.osgeo.org/grass-stable/manuals/d.rast.num.html">d.rast.num</a>,
  <a href="https://grass.osgeo.org/grass-stable/manuals/d.grid.html">d.grid</a>,
  <a href="https://grass.osgeo.org/grass-stable/manuals/d.mon.html">d.mon</a>,
  <a href="https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html">v.mkgrid</a>
</em>

<h2>AUTHOR</h2>

Vaclav Petras, <a href="https://geospatial.ncsu.edu/geoforall/">NCSU GeoForAll Lab</a>
