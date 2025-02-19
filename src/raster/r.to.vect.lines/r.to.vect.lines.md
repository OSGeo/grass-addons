<h2>NOTES</h2>

Extracts rows from a raster map as 3D vector lines.
<p>
Reads a raster map, writes to a vector map.
<p>
Doesn't check if output map already exists. (fixme)
<p>
The category given to the line refers to the row number. (starting with category 0!)
<p>
Nulls within a row are skipped, so holes will be filled by a straight line. (fixme)
Nulls at the ends of lines are not included in the output line.
<p>
Nulls are not handled very well and may sneak through as very negative numbers. (fixme)


<h2>EXAMPLE</h2>

Display a wiggle plot in NVIZ:
<!-- todo: variable area wiggle plots, where negative areas are filled -->
<br>
(Spearfish dataset)

<div class="code"><pre>
g.region raster=elevation.dem
r.to.vect.lines.py in=elevation.dem out=wiggle_lines
eval `v.info -g wiggle_lines`
r.mapcalc "floor = $bottom"
nviz elev=floor vector=wiggle_lines

# alternative
m.nviz.image elevation_map=floor vline=wiggle_lines resolution_fine=1 \
  zexag=20 out=wiggle.png perspective=5
</pre></div>

<img src="r_to_vect_lines_example.png" alt="r.to.vect.lines example">


<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/r.to.vect.html">r.to.vect</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/v.in.lines.html">v.in.lines</a>
</em>


<h2>AUTHOR</h2>

Hamish Bowman<br>
<i>
Dept. of Geology<br>
University of Otago<br>
Dunedin, New Zealand</i>
