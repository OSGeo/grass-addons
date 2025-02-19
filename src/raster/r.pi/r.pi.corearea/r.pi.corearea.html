<h2>DESCRIPTION</h2>

Edge effects and core area analysis of landcover fragments. This module
can compute static edge effects (defined edge depth) and dynamic edge
effects (based on surrounding landscape). The impact of the surrounding
landscape can be accounted for and the resulting core area is provided.

<h2>NOTES</h2>

This module is generating core areas based on defined edge depths. The
edge depths can be increased by the values of a <em>costmap</em> (e.g.
urban areas could have a more severe impact than secondary forest on
forest fragments). Moreover a friction map (<em> propmap</em> within
the fragments can lower the impact of surrounding landcover types and
hence an increased edge depth (e.g. a river or escarpment which might
lower the edge effects). Moreover a <em> dist_weight</em> can be
assigned in order to increase the weight of closer pixel values.

<h3>Distance weight</h3>

The assigned distance weight is computed as:<br>
w(d) = 1 - (d / d_max)^(tan(dist_weight * 0.5 * pi))<br>

where:<br>

<ul>
<li>d = Distance of the respective cell
<li>d_max - the defined maximum distance
<li>dist_weight - the parameter how to weight the pixel values in the landscape depending on the distance <br>
</ul>

the <em>dist_weight</em> has a range between 0 and 1 and results in:

<ul>
<li>0 &lt; dist_weight &lt; 0.5: the weighting curve decreases at low
distances to the fragment and lowers to a weight of 0 at d=d_max

<li>dist_weight = 0.5: linear decrease of weight until weight of 0 at d = d_max

<li>0.5 &lt; dist_weight &lt; 1: the weighting curve decreases slowly
at low distances and approaches weight value of 0 at higher distances
from the fragment, the weight value 0 is reached at d = d_max

<li>dist_weight = 1: no distance weight applied, common static edge
depth used
</ul>


<h3>propmap</h3>

The <em>propmap</em> minimizes the effect of the edge depth and the
surrounding matrix. This has an ecological application if certain
landscape features inside a e.g. forest fragment hamper the human
impact (edge effects). <br>

two methods exist:<br>

<ul>
<li>propmethod=linear: propagated value = actual value - (propmap value at this position)<br>
<li>propmethod=exponential: propagated value = actual value / (propmap value at this position)<br>
</ul>

If 0 is chosen using the linear method, then propagated value=actual
value which results in a buffering of the whole region. In order to
minimize the impact the value must be larger than 1. For the
exponential method a value of below 1 should not be chosen, otherwise
it will be propagated infinitely.

<h2>EXAMPLE</h2>

An example for the North Carolina sample dataset using class 5 (forest):

For the computation of variable edge effects a costmap is necessary
which need to be defined by the user. Higher costs are resulting in higher edge depths:
<div class="code"><pre>
# class - type - costs
#   1	- developed - 3
#   2	- agriculture - 2
#   3	- herbaceous - 1
#   4	- shrubland - 1
#   5	- forest - 0
#   6	- water - 0
#   7	- sediment - 0

r.mapcalc "costmap_for_corearea = if(landclass96==1,3,if(landclass96==2,2,if(landclass96==3,1,if(landclass96==4,1,if(landclass96==5,0,if(landclass96==6,0,if(landclass96==7,0)))))))"

</pre></div>


now the edge depth and the resulting core area can be computed:
<div class="code"><pre>
r.pi.corearea input=landclass96 costmap=costmap_for_corearea  output=landcover96_corearea keyval=5 buffer=5 distance=5 angle=90 stats=average propmethod=linear
</pre></div>


the results consist of 2 files:<br>
landclass96_corearea: the actual resulting core areas<br>
landclass96_corearea_map: a map showing the edge depths

<h2>SEE ALSO</h2>

<em>
<a href="r.pi.grow.html">r.pi.grow</a>,
<a href="r.pi.import.html">r.pi.import</a>,
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
