<h2>DESCRIPTION</h2>

<em>v.what.rast.multi</em> retrieves raster value from a given set of raster map for each point or centroid stored in a given vector map. It can update a <b>column</b> in the linked vector attribute table with the retrieved raster cell value or print it. It is essentially a wrapper around <em>v.what.rast</em>.

<p>The column type needs to be numeric (integer, float, double, ...). If the column doesn't exist in the vector attribute table than the module will create the new column of type corresponding with the input raster map.

<p>
If the <b>-p</b> flag is used, then the attribute table is not updated and the results are printed to standard output.
<p>
If the <b>-i</b> flag is used, then the value to be uploaded to the database is interpolated from the four nearest raster cells values using an inverse distance weighting method (IDW). This is useful for cases when the vector point density is much higher than the raster cell size.

<h2>NOTES</h2>

<p>
Points and centroid with shared category number cannot be processed. To solved this, unique categories may be added with <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.category.html">v.category</a></em> in a separate layer.
<p>
If multiple points have the same category, the attribute value is set to NULL. If the raster value is NULL, then attribute value is set to NULL.
<p>
<em>v.what.rast.multi</em> operates on the attribute table. To modify the vector geometry instead, use <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.drape.html">v.drape</a></em>.
<p>
Categories and values are output unsorted with the print flag. To sort them pipe the output of this module into the UNIX <tt>sort</tt> tool (<tt>sort&nbsp;-n</tt>). If you need coordinates, after sorting use <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html">v.out.ascii</a></em> and the UNIX <tt>paste</tt> tool (<tt>paste&nbsp;-d'|'</tt>). In the case of a NULL result, a "<tt>*</tt>" will be printed in lieu of the value.
<p>
The interpolation flag is only useful for continuous value raster maps, if a categorical raster is given as input the results will be nonsense. Since the search window is limited to four raster cells there may still be raster cell-edge artifacts visible in the results, this compromise has been made for processing speed. If one or more of the nearest four raster cells is NULL, then only the raster cells containing values will be used in the weighted average.


<h2>EXAMPLES</h2>

<h3>Transferring raster values into existing attribute table of vector points map</h3>

Reading values from raster map at position of vector points, writing these values into a column of the attribute table connected to the vector map:
<p>

<div class="code"><pre>
# set computational region
g.region raster=slope -p

# work on copy of original geodetic points map
g.copy vector=geodetic_pts,mygeodetic_pts

# query raster cells
v.what.rast.multi map=mygeodetic_pts raster=elev_state_500m,slope,aspect columns=elevation,slope,aspect

# print results
v.db.select map=mygeodetic_pts columns=elevatin,slope,aspect separator=comma where="SLOPE > 0"

</pre></div>


<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/v.what.rast.html">v.what.rast</a>
</em>


<h2>AUTHOR</h2>

Pierre Roudier<br>
