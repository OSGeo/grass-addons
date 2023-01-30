<h2>DESCRIPTION</h2>

<p>
<em>r.neighborhoodmatrix</em> identifies all adjacency relations between
objects (aka segments or clumps identified by identical integer cell values of
adjacent pixels) in a raster map and exports these as a 2xn matrix
where n is the number of neighborhood relations with each relation listed
in both directions (i.e. if a is neighbor of b, the list will contain
a,b and b,a). If a path to an output file is specified, the matrix will be
written to that file, otherwise it will be sent to standard output.

<p>
Neighborhood relations are determined pixel by pixel, and by default only
pixels that share a common pixel boundary are considered neighbors. When
the <em>-d</em> flag is set pixels sharing a common corner (i.e. diagonal
neighbors) are also taken into account.

<p>
When the <em>-l</em> flag is set, the module additionally indicates the length
of the common border between two neighbors in number of pixels. As this length
is not clearly defined for diagonal neighbors, the <em>-l</em> flag cannot
be used in combination with the <em>-d</em> flag.

<p>
The <em>-c</em> flag currently adds column headers. Please note that <b>this
flag's meaning will be inversed when GRASS 8 comes out</b> in order to
harmonize its behaviour with that in other modules.


<h2>NOTES</h2>

<p>
As neighborhood length is measured in pixels, this length is not in proportion
to length in map units if the location is a lat-long location, or if the
resolution is not the same in East-West and in North-South direction
(rectangular pixels).

<p>
The module respects the region settings, so if the raster map is outside the
current computational region, the resulting list of neighbors will be empty.


<h2>TODO</h2>

<ul>
	<li>Add flag to only output half matrix with each relation only shown
		once.</li>
	<li>Measure neighbordhood length in map units, not only pixels</li>
</ul>

<h2>EXAMPLE</h2>

<p>
Start by making sure the input map is of type CELL:
<div class="code"><pre>
r.mapcalc "bc_int = int(boundary_county_500m)"
</pre></div>

<p>
Send the neighborhood matrix of the counties in the boundary_county map of the
North Carolina dataset to standard output:

<div class="code"><pre>
r.neighborhoodmatrix in=bc_int sep=comma
</pre></div>

<p>
Idem, but also calculating neighborhood length, sending the output to a file:

<div class="code"><pre>
r.neighborhoodmatrix -l n=bc_int sep=comma output=county_neighbors.csv
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="v.neighborhoodmatrix.html">v.neighborhoodmatrix</a>
</em>

<h2>AUTHORS</h2>

Original Python-Version: Moritz Lennert<br>
C-Version: Markus Metz
