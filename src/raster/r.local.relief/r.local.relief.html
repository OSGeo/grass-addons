<h2>DESCRIPTION</h2>

<p><em>r.local.relief</em> generates a local relief model (LRM) from lidar-derived high-resolution DEMs. Local relief models enhance the visibility of small-scale surface features by removing large-scale landforms from the DEM.</p>

<p>Generating the LRM is accomplished in 7 steps (Hesse 2010:69):</p>
<ol>
    <li>Creation of the DEM from the LIDAR data. Buildings, trees and other objects on the earth's surface should be removed.</li>
    <li>Apply a low pass filter to the DEM. The low pass filter approximates the large-scale landforms. The neighborhood size of the low pass filter determines the scale of features that will be visible in the LRM. A default neighborhood size of 11 is used.</li>
    <li>Subtract the low-pass filter result from the DEM to get the local relief.</li>
    <li>Extract the zero contour lines from the difference map.</li>
    <li>Extract the input DEM's elevation values along the zero contour lines.</li>
    <li>Create a purged DEM by interpolating the null values between the rasterized contours generated in the previous step. This layer represents the large-scale landforms that will be removed to expose the local relief in the final step.</li>
    <li>Subtract the purged DEM from the original DEM to get the local relief model.</li>
</ol>
<p>
The interpolation step is performed by the <em><a href="https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html">r.fillnulls</a></em> module by default (using cubic interpolation).
If this is not working on your data, you can use <em>-v</em> flag to use <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.bspline</a></em> cubic interpolation instead (this might be slower on some types of data).
</p>

<h2>OUTPUT</h2>
<p>
The final local relief model is named according to the <em>output</em> parameter.
When the <em>-i</em> flag is specified, <em>r.local.relief</em> creates additional
output files representing the intermediate steps in the LRM generation process.
The names and number of the intermediate files vary depending
on whether <em><a href="https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html">r.fillnulls</a></em> (default)
or <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.bspline</a></em>
(specified by using the <em>-v</em> flag) is used for interpolation.
The intermediate maps are composed of the user-specified <em>output</em>
parameter and suffixes describing the intermediate map.</p>

<p>Without using the <em>-v</em> flag
(<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html">r.fillnulls</a></em> interpolation),
intermediate maps have the following suffixes:</p>
<ul>
    <li><tt>_smooth_elevation</tt>: The result of running the low pass filter on the DEM.</li>
    <li><tt>_subtracted_smooth_elevation</tt>: The result of subtracting the low pass filter map from the DEM.</li>
    <li><tt>_raster_contours_with_values</tt>: The rasterized zero contours with the values from elevation map.</li>
    <li><tt>_purged_elevation</tt>: The raster interpolated from the _raster_contours_with_values map based that represents the large-scale landforms.</li>
</ul>

<p>With using the <em>-v</em> flag
(<em><a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.bspline</a></em> interpolation),
intermediate maps have the following suffixes:</p>
<ul>
    <li><tt>_smooth_elevation</tt>: The result of running the low pass filter on the DEM.</li>
    <li><tt>_subtracted_smooth_elevation</tt>: The result of subtracting the low pass filter map from the DEM.</li>
    <li><tt>_vector_contours</tt>: The zero contours extracted from the DEM.</li>
    <li><tt>_contour_points</tt>: The points extractacted along the zero contour lines with the input DEM elevation values.</li>
    <li><tt>_purged_elevation</tt>: The raster interpolated from the _contour_points map that represents the large-scale landforms.</li>
</ul>

<p>
The module sets equalized gray scale color table for local relief model map
and for the elevation difference (subtracted elevations). The color tables
of other raster maps are set to the same color table as the input elevation map has.

<h2>EXAMPLE</h2>

Basic example using the default neighborhood size of 11:
<div class="code"><pre>
r.local.relief input=elevation output=lrm11
</pre></div>
Example with a custom neighborhood size of 25:
<div class="code"><pre>
r.local.relief input=elevation output=lrm25 neighborhood_size=25
</pre></div>
Example using the default neighborhood size of 11 and saving the intermediate maps:
<div class="code"><pre>
r.local.relief -i input=elevation output=lrm11
</pre></div>
Example using the default neighborhood size of 11 with bspline interpolation and saving the intermediate maps:
<div class="code"><pre>
r.local.relief -i -v input=elevation output=lrm11
</pre></div>
Example in NC sample location (area of Raleigh downtown):
<div class="code"><pre>
# set the computational region to area of interest
g.region n=228010 s=223380 w=637980 e=644920 res=10

# compute local relief model
r.local.relief input=elevation output=elevation_lrm

# show the maps, e.g. using monitors
d.mon wx0
d.rast elevation
d.rast elevation_lrm

# try alternative red (negative values) and blue (positive values) color table
# color table shows only the high values which hides small streets
# for non-unix operating systems use file or interactive input in GUI
# instead of rules=- and EOF syntax
r.colors map=elevation_lrm@PERMANENT rules=- &lt;&lt;EOF
100% 0:0:255
0 255:255:255
0% 255:0:0
nv 255:255:255
default 255:255:255
EOF
</pre></div>

<!--
images generated using the example above
saved from map display
resized to 500x500 with keep ratio in Nautilus
-->
<center>
<img src="r.local.relief.png" alt="Local relief in NC location (gray scale)">
<img src="r.local.relief_redblue.png" alt="Local relief in NC location (red blue)">
<p>
Figure: Local relief model of downtown Raleigh area created from elevation raster
map in NC sample location with the default (gray scale) color table
and custom red (negative values) and blue (positive values) color table
</center>


<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a>,
<a href="r.shaded.pca.html">r.shaded.pca</a>,
<a href="r.skyview.html">r.skyview</a>
</em>


<h2>REFERENCES</h2>
<ul>
    <li>Hesse, Ralf (2010).
    LiDAR-derived Local Relief Models - a new tool for archaeological prospection.
    <em>Archaeological Prospection</em> 17:67-72.</li>
    <li>Bennett, Rebecca (2011).
    <em>Archaeological Remote Sensing: Visualization and Analysis of grass-dominated environments using laser scanning and digital spectra data.</em> Unpublished PhD Thesis. Electronic Document,
    <a href="http://eprints.bournemouth.ac.uk/20459/1/Bennett%2C_Rebecca_PhD_Thesis_2011.pdf">http://eprints.bournemouth.ac.uk/20459/1/Bennett%2C_Rebecca_PhD_Thesis_2011.pdf</a>,
    Accessed 25 February 2013.
    (provided bash script with <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html">v.surf.bspline</a></em>-based implementation)</li>
</ul>

<h2>AUTHORS</h2>

<p>
Vaclav Petras, <a href="http://gis.ncsu.edu/osgeorel/">NCSU OSGeoREL</a>,<br>
Eric Goddard
