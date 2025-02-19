<h2>DESCRIPTION</h2>

<em>r.forestfrag</em> Computes the forest fragmentation following
the methodology proposed by Riitters et al. (2000). See
<a href="https://www.ecologyandsociety.org/vol4/iss2/art3/">this article</a> for a
detailed explanation.

<p>It follows a "sliding window" algorithm with overlapping windows.
The amount of forest and its occurrence as adjacent forest pixels
within fixed-area "moving-windows" surrounding each forest pixel is
measured. The window size is user-defined. The result is stored at
the location of the center pixel. Thus, a pixel value in the derived
map refers to "between-pixel" fragmentation around the corresponding
forest location.

<p>As input it requires a binary map with (1) forest and (0)
non-forest. Obviously, one can replace forest any other land cover
type. If one wants to exclude the influence of a specific land cover
type, e.g., water bodies, it should be classified as no-data (NA) in
the input map. See e.g.,
<a href="https://pvanb.wordpress.com/2016/03/25/update-of-r-forestfrag-addon/">blog post</a>.

<p>Let <em>Pf</em> be the proportion of pixels in the window that
are forested. Define <em>Pff</em> (strictly) as the proportion of
all adjacent (cardinal directions only) pixel pairs that include at
least one forest pixel, for which both pixels are forested. <em>Pff</em>
 thus (roughly) estimates the conditional probability that,
given a pixel of forest, its neighbor is also forest. The
classification model then identifies six fragmentation categories as:

<div class="code"><pre>
interior:       Pf = 1.0
patch:          Pf &lt; 0.4
transitional:   0.4 &le; Pf &lt; 0.6
edge:           Pf &ge; 0.6 and Pf - Pff &lt; 0
perforated:     Pf &ge; 0.6 and Pf - Pff &gt; 0
undetermined:   Pf &ge; 0.6 and Pf = Pff
</pre></div>

<h2>NOTES</h2>

<ul>
<li>The moving window size is user-defined (default=3)
and must be an odd number. If an even number is given, the function
will stop with an error message.
<li>No-data cells are ignored. This means that statistics at the
raster edges are based on fewer cells (smaller) moving windows. If this
is a problem, the user can choose to have the output raster trimmed
with a number of raster cells equal to 1/2 * the size of the moving
window.
<li>The function respects the region. However, the user has the option
to set the region to match the input layer.
</ul>


<h2>EXAMPLE</h2>

In the North Carolina sample Location, set the computational region
to match the land classification raster map:

<div class="code"><pre>
g.region raster=landclass96
</pre></div>

Then mark all cells which are forest as 1 and everything else as zero:

<div class="code"><pre>
r.mapcalc "forest = if(landclass96 == 5, 1, 0)"
</pre></div>

Use the new forest presence raster map to compute the forest
fragmentation index with window size 7:

<div class="code"><pre>
r.forestfrag input=forest output=fragmentation window=7
</pre></div>

<center>
<img src="r_forestfrag_window_7.png" alt="r.forestfrag output with window size 7">
<img src="r_forestfrag_window_11.png" alt="r.forestfrag output with window size 11">
<p><em>
Two forest fragmentation indices with window size 7 (left) and
11 (right) show how increasing window size increases the amount of
edges.
</em></p>
</center>


<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html">r.mapcalc</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/r.li.html">r.li</a>
</em>

<p>
The addon is based on the
<a href="https://grasswiki.osgeo.org/wiki/AddOns/GRASS_6#r.forestfrag">
r.forestfrag.sh</a> script, with as extra options user-defined
moving window size, option to trim the region (by default it
respects the region) and a better handling of no-data cells.

<h2>REFERENCES</h2>
Riitters, K., J. Wickham, R. O'Neill, B. Jones,
and E. Smith. 2000. Global-scale patterns of forest fragmentation.
Conservation Ecology 4(2): 3. [online] URL:
<a href="https://www.consecol.org/vol4/iss2/art3/">https://www.consecol.org/vol4/iss2/art3/</a>

<h2>AUTHORS</h2>


Emmanuel Sambale (original shell version)<br>
Stefan Sylla (original shell version)<br>
Paulo van Breugel (Python version, user-defined moving window size)<br>
Vaclav Petras (major code clean up)
