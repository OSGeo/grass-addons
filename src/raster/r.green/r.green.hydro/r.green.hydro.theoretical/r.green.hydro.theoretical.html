<h2>DESCRIPTION</h2>
<em>r.green.hydro.theoretical</em> calculates for each basin the theoretical maximum hydropower energy potential based on the input raster files with discharge data along a river network and digital terrain elevation models of the considered region.<br>
If there are already existing plants, the function computes the potential installed power in the available parts of the rivers.<br>
This module returns two output vector maps with the available river segments and the optimal position of the plants with their potential maximum powers, intakes and restitutions.<br>
In this module the output is the theoretical maximum hydropower energy that can be converted in the ideal case without considering the efficiency of energy transformation.<br><br>

<h2>NOTES</h2>

The required inputs are the elevation raster map, the river discharge raster map and the value for the minimum size of the exterior watershed basin.<br>
You can optionally add vector maps of existing river networks and lakes that will be considered in the calculation and make the output more realistic.<br>
Instead of the minimum size of the exterior watershed basin you can also enter the basin and stream maps created by r.watershed.<br><br>

<h2>EXPLANATION</h2>

The maximum potential hydropower establishes the theoretical maximum of energy that the study basin can produce assuming that all water resources are used to produce energy.<br>
In real life this situation does not arise, because of environmental flows, other water uses and economic cost analysis.<br><br>

The underlying methods of calculation explained below are based on the considerations and formulas used in the article "A GIS-based assessment of maximum potential hydropower production in La Plata Basin under global changes" written by M. Peviani, I. Popescu, L. Brandimarte, J.Alterach and P. Cuya. <br><br>

The maximum potential hydropower at subbasin scale can be computed as the sum of two components:<br><br>

- upstream subbasin potential &nbsp; &nbsp; &nbsp; &nbsp; &nbsp; - subbasin own potential<br><br>

According to the general schematization in the figure below, point A is the closure point of the upstream subbasins (named UPSTREAM 1, UPSTREAM 2 and UPSTREAM 3).<br>
The three rivers belonging to the three upstream basins merge into the common river of the downstream basin in point A (named Upstreamclosure point).<br>
The downstream basin is bounded by the two closure points A and B.<br>
The scheme divides the subbasins in upper portions, whose energy production is only given by their own potential and a lower portion, whose energy production is the sum of the two components, own potential and the potential given by the flow coming from the upper portions.<br><br>

<center>
<img src="r_green_hydro_theoretical_streams.png" alt="structure"><br><br>
Subbasin scheme to calculate maximum potential hydropower
</center><br><br>

The maximum potential hydropower for the upstream subbasins is given by the energy formula applied to the upstream inflows:<br><br>

<center>
<i><BIG>E<SUB>own_max</SUB> = conv * g * &eta; * Q<SUB>up_hydro</SUB> * (H<SUB>mean</SUB> - H<SUB>closure</SUB>)</BIG></i><br>
<blockquote><Small>where conv is the adimensional conversion factor to calculate energy in GWh (conv = 0.00876);<br>
g is a gravity constant (9.81 m/s<sup>2</sup>);<br>
&eta; is the overall electrical efficiency;<br>
Q<SUB>up_hydro</SUB> is the mean annual discharge at the closure section for the upstream subbasin;<br>
H<SUB>mean</SUB> is the mean elevation of the upstream subbasin calculated from the hypsographic curve, using the statistical tool of Arc-GIS;<br>
H<SUB>closure</SUB> is the elevation at the closure point (point A in the figure);</Small><br><br></blockquote></center>

The downstream lower subbasin (between point A and B in the figure) has both energy components: the potential from the upstream subbasins and its own potential. The own potential is calculated taking into account the discharge coming from the sides of the downstream lower subbasin and the difference between the elevation of the lower subbasin and the elevation at the closure point (point B in the figure):<br><br>

<center>
<i><BIG>E<SUB>own_max</SUB> = conv * g * &eta; * Q<SUB>aff</SUB>  * (H<SUB>mean</SUB> - H<SUB>closure</SUB>)</BIG></i><br>
<blockquote><Small>where Q<SUB>aff</SUB> is the afferent discharge (own lower subbasin discharge). The afferent discharge is the difference of the discharge observed at the
closure section (point B in the figure) and the sum of the upstream discharges;<br>
H<SUB>mean</SUB> is the elevation of lower subbasin;<br>
H<SUB>closure</SUB> is the elevation at closure point (point B in the figure);</Small><br><br></blockquote></center>

The upstream component to the potential of the downstream lower subbasin is calculated taking into account the discharge coming from the upstream subbasins and the difference between the elevation of the upstream closure point (point A in the figure) and the elevation at the basin closure (point B in the figure):<br><br>

<center>
<i><BIG>E<SUB>up_max</SUB> = conv * g * &eta; * &sum;Q<SUB>up_hydro</SUB> * (H<SUB>up_closure</SUB> - H<SUB>closure</SUB>)</BIG></i><br>
<blockquote><Small>where Q<SUB>up_hydro</SUB> is the sum of the mean annual discharges coming from the upstream subbasins;<br>
H<SUB>up_closure</SUB> is the elevation at the upstream closure point (point A in the figure);<br>
H<SUB>closure</SUB> is the elevation at closure point (point B in the figure);</Small><br><br></blockquote></center>

The total maximum hydropower potential of the overall given basin is the sum of the different contributions computed at the subbasin level:<br><br>

<center>
<i><BIG>E<SUB>total_max</SUB> = E<SUB>own_max</SUB> + E<SUB>up_max</SUB></BIG></i><br><br></center>

<h2>EXAMPLES</h2>

<b>EXAMPLE 1</b><br><br>

This example is based on the case-study of the Gesso and Vermenagna valleys located in the Piedmont Region, in South-West Italy, close to the Italian and French border.<br><br>

In the map below you can see the input files elevation and natural discharge.<br><br>

<center><br>
<img src="r_green_hydro_theoretical_input.png" alt="input"><br><br>
input raster map with elevation and natural discharge
</center><br><br>

For a faster run of this example, the input maps elevation and discharge are limited to the section that can be modified by r.green.hydro.theoretical using the code<br>
r.mask vector=boundary.<br><br>

To create the map of this example, you can type in the following code in the command console or if you prefer you can only type in the main function r.green.hydro.theoretical in the console and specify the other parameters of the code like elevation or discharge by using the graphical user interface.<br>
<div class="code"><pre>
r.green.hydro.theoretical elevation=elevation discharge=naturaldischarge rivers=streams lakes=lakes basins=basin stream=stream output=out</pre></div><br>

In the map below, you can see the output vector map with the basin potential.<br><br>
<center><br>
<img src="r_green_hydro_theoretical_output.png" alt="output park"><br><br>
output vector map with basin potential
</center><br><br>

<h2>SEE ALSO</h2>
<em>
<a href="r.green.hydro.discharge.html">r.green.hydro.discharge</a><br>
<a href="r.green.hydro.delplants.html">r.green.hydro.delplants</a><br>
<a href="r.green.hydro.optimal.html">r.green.hydro.optimal</a><br>
<a href="r.green.hydro.recommended.html">r.green.hydro.recommended</a><br>
<a href="r.green.hydro.structure.html">r.green.hydro.structure</a><br>
<a href="r.green.hydro.technical.html">r.green.hydro.technical</a><br>
<a href="r.green.hydro.financial.html">r.green.hydro.financial</a><br>
</em>

<h2>AUTHORS</h2>

Giulia Garegnani (Eurac Research, Bolzano, Italy), Manual written by Sabrina Scheunert.<br>
