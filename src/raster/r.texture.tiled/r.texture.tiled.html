<h2>DESCRIPTION</h2>

<em>r.texture.tiled</em> cuts a raster input map into tiles and runs
<a href="https://grass.osgeo.org/grass-stable/manuals/r.texture.html">r.texture</a> over these tiles before patching the
result together into a single output raster map.

<p>
The overlap between tiles is calculated internally in order to correspond to
the window <b>size</b> in order to avoid any border effects.

<p>
Tiles can be defined with the <b>tile_width</b>, <b>tile_height</b> and
<b>overlap</b> parameters. If <b>processes</b> is higher than one, these tiles
will be processed in parallel.

<p>
The <b>mapset_prefix</b> parameter allows to make sure that the temporary
mapsets created during the tiled processing have unique names. This is useful
if the user runs <em>r.texture.tiled</em> several times in parallel (e.g. in
an HPC environment).

<h2>NOTES</h2>

The parameters for texture calculation are identical to those of
<a href="https://grass.osgeo.org/grass-stable/manuals/r.texture.html">r.texture</a>. Currently, this module only allows
calculating one texture feature at a time. The <b>n</b> flag allowing null
cells is automatically set in order to avoid issues at the border of the
current computational region / of the input map.

<h2>EXAMPLE</h2>

Run r.texture over tiles with size 1000x1000 using 4 parallel processes:

<div class="code"><pre>
g.region rast=ortho_2001_t792_1m
r.texture.tiled ortho_2001_t792_1m output=ortho_texture method=idm \
   tile_width=1000 tile_height=1000 processes=4
</pre></div>

<h2>SEE ALSO</h2>

<a href="https://grass.osgeo.org/grass-stable/manuals/r.texture.html">r.texture</a>

<h2>AUTHOR</h2>

Moritz Lennert
