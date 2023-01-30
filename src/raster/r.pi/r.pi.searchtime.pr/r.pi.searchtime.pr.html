
<h2>DESCRIPTION</h2>

Analysis of patch relevance to maintain the landscape connectivity
using individual-based dispersal model for connectivity analysis
(time-based).
<p>
This modules provides information about the importance of single
patches for maintaining the connectivity of individual fragments
derived of a landcover classification. Unlike <em>r.pi.energy.pr</em>
this module provides information about the differences in time from
emigration to immigration. The individual based dispersal model results
are based on the step length and range, the perception distance and the
attractivity to move towards patches.

<h2>NOTES</h2>

The suitability matrix impacts the step direction of individuals. If
individuals are moving beyond the mapset borders the indivuals are set
back to their original source patches.

<h2>EXAMPLE</h2>

An example for the North Carolina sample dataset:
<p>
The patch relevance concerning connectivity are based on patches of the
<em>landclass96</em> raster class 5 amd the time (amount of steps) from
emigration to immigration is computed. The step length is set to 5
pixel, the output statistics are set to <em>average</em> time and
<em>variance</em> of searchtime. For each patch 1000 individuals were
released and the model stopped when at least 80% of all individuals
sucessfully immigrated:<br>
<div class="code"><pre>
r.pi.searchtime.pr input=landclass96 output=searchtime_iter1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average
</pre></div>

setting the perception range to 10 pixel:
<div class="code"><pre>
r.pi.searchtime.pr input=landclass96 output=searchtime_iter1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average perception=10
</pre></div>

increasing the attraction to move towards patches to 10:
<div class="code"><pre>
r.pi.searchtime.pr input=landclass96 output=searchtime_iter1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average multiplicator=10
</pre></div>

output of each movement location for a defined step frequency. Here every 10th step is provided as output raster:
<div class="code"><pre>
r.pi.searchtime.pr input=landclass96 output=searchtime_iter1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average out_freq=10
</pre></div>

output of a raster which immigration counts:
<div class="code"><pre>
r.pi.searchtime.pr input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average out_immi=immi_counts
</pre></div>

the previous examples assumed a homogeneous matrix, a heterogenous
matrix can be included using a raster file which values are taken as
costs for movement (0-100):
<div class="code"><pre>
# it is assumed that our species is a forest species and cannot move
# through water, hence a cost of 100, does not like urban areas
# (class: 6, cost: 10) but can disperse through shrubland (class 4,
# cost=1) better than through grassland (class 3, cost: 2):

r.mapcalc "suit_raster = if(landclass96==5,1,if(landclass96 == 1, 10, if (landclass96==3,2, if(landclass96==4,1,if(landclass96==6,100)))))"
r.pi.searchtime.pr input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 dif_stats=average suitability=suit_raster
</pre></div>


<h2>SEE ALSO</h2>

<em>
<a href="r.pi.searchtime.html">r.pi.searchtime</a>,
<a href="r.pi.searchtime.mw.html">r.pi.searchtime.mw</a>,
<a href="r.pi.html">r.pi</a>
</em>

<h2>AUTHORS</h2>

Programming: Elshad Shirinov<br>
Scientific concept: Dr. Martin Wegmann <br>
Department of Remote Sensing <br>
Remote Sensing and Biodiversity Unit<br>
University of Wuerzburg, Germany
<p>
Port to GRASS GIS 7: Markus Metz
