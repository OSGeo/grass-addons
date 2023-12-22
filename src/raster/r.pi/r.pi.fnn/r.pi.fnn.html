<h2>DESCRIPTION</h2>

Determine the functional nearest-neighbor distance analysis.

<em>r.pi.fnn</em> is a patch based ecological/functional nearest
neighbour analysis module. It computes distance based on a friction
map. This module is related to <em>r.pi.enn</em> but more adequate if
the ecological connectivity should be analysed.

<h2>NOTES</h2>

The calculation of the ecolgogical nearest neighbour is based on a raster
with start patches. The actual map can be categorical or continuous but
the value defined in <em>keyval</em> will be the basis for the patches
to calculate the methods defined below. These patches will also be in
the output map.

The calculation of the ecolgogical nearest neighbour is based on a costmap
(* and 1-infinite) - this map can be binary or continous - high values
are considered to have high cost issues and the shortest path is the
one with the lowest amount of costs. "null" values can not be traversed,
hence these values have to be bypassed. "0" values are not accepted and
will result in "0" distance.

<p>
e.g. if a binary map(1 and 2) is used, the the path with the
lowest amount of "1" is chosen

The <em>number</em> is the amount of nearest neighbours to be taken and
the calculated distances are processed as assigned in <em>statmethod</em>

Operations which <em>r.pi.fnn</em> can perform are:

<p>

<dl>
<dt><b>Distance</b>

<dd>The <em>Distance to Nearest</em> computes the nearest edge-to-edge
distance between patches. Counting from the focus patch.

<dt><b>path Distance</b>

<dd>The <em>Distance to Nearest</em> computes the nearest edge-to-edge
distance between patches. Unlike <em>Distance</em> the distance is
computed based on subsequent NN not from the focus patch onwards. The
1th NN is the first patch with the minimal edge-to-edge distance from
the focus patch, while 2th NN is the patch with the minimal edge-to-edge
distance from the 1th NN patch and so on.

<dt><b>Area</b>

<dd>The <em>Area</em> computes the size of the nearest edge-to-edge
distance patch. It is based on <em>Distance</em> not on <em>path Distance</em>.

<dt><b>Perimeter</b>

<dd>The <em>Perimeter</em> computes the Perimeter of the nearest
edge-to-edge distance patch. It is based on <em>Distance</em> not on
<em> path Distance</em>.

<dt><b>SHAPE</b>

<dd>The <em>SHAPE</em> computes the SHAPE Index of the nearest edge-to-edge
distance patch. It is based on <em>Distance</em> not on <em> path Distance</em>.
</dl>

The <em>statsmethod</em> operators determine calculation is done on the
distance. <em>Average</em>, <em>Variance</em>,<em>Stddev</em> and
<em>value</em> can be used.

<dl>
<dt><b>Average</b>

<dd>The <em>Average</em> computes the average value defined in
<em>Operations to perform </em>.

<dt><b>Variance</b>

<dd>The <em>Variance</em> computes the variance defined in
<em>Operations to perform </em>.

<dt><b>Stand. Dev.</b>

<dd>The <em>Stand. Dev.</em> computes the stddev value defined in
<em>Operations to perform </em>.

<dt><b>Value</b>

<dd>The <em>patch Distance</em> computes the nearest edge-to-edge distance
between two patches. The output of <em>value</em> is the actual value.
E.g. NN==5 of <em>area</em> gives the size of the 5th NN while
<em>Average</em> gives the average of the area of 1-5th NN.
</dl>

The input options are either one NN: <em>1</em> or several NN separated
by <em>,</em>: 1,2,5,8 or a range of NN: 1-6.

<p>
Merging these options is possible as well: 1-5,8,9,13,15-19,22 etc.

<h2>EXAMPLE</h2>

An example for the North Carolina sample dataset:

Computing the functional or ecological distance to the first to nth
nearest neighrbours using a cost matrix:
<div class="code"><pre>
r.mapcalc "cost_raster = if(landclass96==5,1,if(landclass96 == 1, 10, if (landclass96==3,2, if(landclass96==4,1,if(landclass96==6,100)))))"
r.pi.fnn input=landclass96 keyval=5 costmap=cost_raster output=fnn1 method=distance number=10 statmethod=average
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="r.pi.enn.html">r.pi.enn</a>,
<a href="r.pi.index.html">r.pi.index</a>,
<a href="r.pi.html">r.pi</a>
</em>

<h2>AUTHORS</h2>

Programming: Elshad Shirinov<br>
Scientific concept: Dr. Martin Wegmann<br>
Department of Remote Sensing<br>
Remote Sensing and Biodiversity Unit<br>
University of Wuerzburg, Germany
<p>
Port to GRASS GIS 7: Markus Metz
