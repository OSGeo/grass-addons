# r.survey.py


<html>


<h2>NAME</h2>
<em><b>r.survey.py</b></em>  - Returns maps of visibility indexes (3d distance, view angle and solid angle) from multiple survey points
<h2>KEYWORDS</h2>
<a href="visibility.html">visibility</a>, <a href="topic_survey.html">survey</a>
<h2>SYNOPSIS</h2>
<div id="name"><b>r.survey.py</b><br></div>
<b>r.survey.py --help</b><br>
<div id="synopsis"><b>r.survey.py</b> [-<b>bcd</b>] <b>points</b>=<em>name</em> <b>dem</b>=<em>name</em> <b>output</b>=<em>name</em> <b>maxdist</b>=<em>float</em>  [<b>treesmap</b>=<em>name</em>]   [<b>buildingsmap</b>=<em>name</em>]  <b>obs_heigh</b>=<em>string</em>  [<b>treesheigh</b>=<em>string</em>]  [<b>treesheighdeviation</b>=<em>string</em>]   [<b>buildingsheigh</b>=<em>string</em>]   [<b>obsabselev</b>=<em>string</em>]   [<b>layer</b>=<em>string</em>]  <b>viewangle_threshold</b>=<em>string</em>  [<b>object_radius</b>=<em>string</em>]   [<b>nprocs</b>=<em>integer</em>]   [<b>memory</b>=<em>integer</em>]   [--<b>overwrite</b>]  [--<b>help</b>]  [--<b>verbose</b>]  [--<b>quiet</b>]  [--<b>ui</b>] 
</div>

<div id="flags">
<h3>Flags:</h3>
<dl>
<dt><b>-b</b></dt>
<dd>Create a simple visible-not visible raster map</dd>

<dt><b>-c</b></dt>
<dd>Consider the curvature of the earth (current ellipsoid)</dd>

<dt><b>-d</b></dt>
<dd>allow only downward view direction (can be used for drone view)</dd>

<dt><b>--overwrite</b></dt>
<dd>Allow output files to overwrite existing files</dd>
<dt><b>--help</b></dt>
<dd>Print usage summary</dd>
<dt><b>--verbose</b></dt>
<dd>Verbose module output</dd>
<dt><b>--quiet</b></dt>
<dd>Quiet module output</dd>
<dt><b>--ui</b></dt>
<dd>Force launching GUI dialog</dd>
</dl>
</div>

<div id="parameters">
<h3>Parameters:</h3>
<dl>
<dt><b>points</b>=<em>name</em>&nbsp;<b>[required]</b></dt>
<dd>Name of input vector map</dd>
<dd>Name of the input points map  (representing the survey location). It can not be a 3D vector layer.</dd>

<dt><b>dem</b>=<em>name</em>&nbsp;<b>[required]</b></dt>
<dd>Name of the input DEM layer</dd>

<dt><b>output</b>=<em>name</em>&nbsp;<b>[required]</b></dt>
<dd>Prefix for the output visibility layers</dd>

<dt><b>maxdist</b>=<em>float</em>&nbsp;<b>[required]</b></dt>
<dd>max distance from the input points</dd>
<dd>Default: <em>1000</em></dd>

<dt><b>treesmap</b>=<em>name</em></dt>
<dd>Name of input vector map</dd>
<dd>Name of the vector layer representing the forested areas</dd>

<dt><b>buildingsmap</b>=<em>name</em></dt>
<dd>Name of input vector map</dd>
<dd>Name of the vector layer representing the buildings</dd>

<dt><b>obs_heigh</b>=<em>double</em>&nbsp;<b>[required]</b></dt>
<dd>observer_elevation</dd>
<dd>Default: <em>1.75</em></dd>

<dt><b>treesheigh</b>=<em>string</em></dt>
<dd>field of the attribute table containing information about threes heigh</dd>

<dt><b>treesheighdeviation</b>=<em>string</em></dt>
<dd>field of the attribute table containing information about standard deviation value relate to the heigh</dd>

<dt><b>buildingsheigh</b>=<em>string</em></dt>
<dd>field of the attribute table containing information about buildings heigh</dd>

<dt><b>obsabselev</b>=<em>string</em></dt>
<dd>field of the attribute table containing information about observer absolute elevation above the same datum used by the DEM (e.g. geodetic elevation)</dd>

<dt><b>layer</b>=<em>string</em></dt>
<dd>layer of the attribute table of the point map (can be usefull for obsabselev option)</dd>
<dd>Default: <em>1</em></dd>

<dt><b>viewangle_threshold</b>=<em>double</em>&nbsp;<b>[required]</b></dt>
<dd>cut the output layers at a given threshold value (between 90 and 180 degrees)</dd>
<dd>Default: <em>90.01</em></dd>

<dt><b>object_radius</b>=<em>double</em></dt>
<dd>radius of the surveyed object in unit of map (default is half the DEM resolution)</dd>

<dt><b>nprocs</b>=<em>integer</em></dt>
<dd>Number of processes</dd>
<dd>Default: <em>1</em></dd>

<dt><b>memory</b>=<em>integer</em></dt>
<dd>Amount of memory to use in MB (for r.viewshed analysis)</dd>
<dd>Default: <em>500</em></dd>

</dl>

<h2>DESCRIPTION</h2>

r.survey is aimed at earth surface analysis. It is useful for evaluating the visibility (in terms of 3D Distance, Solid Angle and orientation of the terrain respect to the line of sight) of  features lying on the terrain slope, like landslides, road cuts, minor vegetation, mining activity, geological outcrops, surface pipelines, parking areas, solar panels plants, burned areas, etc. 
<p>
Depending on the purpose of the study, one can be interested in searching the closest position to observe a given territory while for others, having a frontal view can be more relevant. In some cases, the objective could be the combined balance between the closest and the most frontal view, in order to evaluate how much of the human field of view is occupied by a given object (solid angle). 
<p>
r.survey is deeply based on the powerfull r.viewshed GRASS GIS module. 
<p>
r.survey wants to provide the user the necessary information to answer questions such as:
<p>
In a survey trip, from how many places is something visible?
<p>
During a field work, which place would be the best position to observe a given point/area (according to the distance, the angle or both)?
<p>
Which portion of the territory is visible along a survey path/flight?
<p>
Are objects of a given size visible from a survey path/flight?
<p>
<p>
Three principal outputs (visibility indexes) are given, based on trigonometric calculations in order to provide qualitative and quantitative information about how the terrain is perceived from the selected observation point (or viewpoint). 
This information concerns the three-dimensional distance, the relative orientation (View Angle) and the Solid Angle, of each target pixel with respect to the viewpoint.
<p>
A map containing a set of points describing the locations of the observer and a digital elevation model (DEM) are the mandatory inputs for r.survey. <b>It is very importante that all observation points have different categories, i.e. cat values (see the examples below)</b>.
In addition, maps of buildings and trees, portraying height information, can be used to alter the DEM. In the case of trees map, apart from the height value, a third column in the attribute table has to contain the standard deviation value related to the heigh. This is used to simulate the rougness of forested areas.  
<p>
Many other options can be set according to the aim of the analysis, such as: observer height respect to the ground or respect to an elevation datum (absolute elevation), maximum distance to perform the calculations, a view-angle threshold to exclude, a priori, cell oriented almost perpendicularly to the lines of sight, the average size of the observed object.
The input points map must be provided to the tool as a vector layer. In case it represents the positions of a UAV, an helicopter or of a satellite, it must include an attribute field containing absolute elevation values with respect to a vertical datum (the same datum used by the input DEM). Observer height (respect to the ground, the default is 1.75 m) and maximum distance of observation (default is 1000 m)  are parameters needed by the r.viewshed module. The object radius is used to approximate, with an equivalent circle, the minimum size of an object centered in the cells center and oriented according to the slope and aspect of the cells. Since r.survey produces different types of outputs, a name to be used for the prefix of the output maps is requested.

<p>
<p>
	
3D Distance is the three dimensional linear distance between a viewpoint and a target pixel (see the illutratio bellow). The min3dDistance map portrays  the value of the minimum three-dimensional distance between each pixel and the closest viewpoint, in meters. 
<p>
	
<img src="r.survey_figures/fig_2.png" alt="e3Ddistance">

<p>
Given a viewpoint, r.survey calculate the unit vector describing direction and sense of the line of sight between that viewpoint and each visible pixel (see illustration bellow). We define View Angle as the angle between the line of sight unit vector and the versor normal to the terrain surface in each pixel. The maxViewAngle map shows the value of the maximum View Angle between each pixel and the viewpoints, in degrees. It is a measure of the most frontal view each single cell is visible from.  View angle output is always larger than 90\B0 and smaller than 180\B0.
<p>
	
<img src="r.survey_figures/View_Angle.png" alt="view angle">


<p>
Solid Angle is one of the best and most objective indicators for quantifying the visibility. The idea is that any observed object will be progressively less apreciable the more far away and the more tilted it is with regard to the viewpoint. As a consequence Solid Angle depends on the size of the observed object as well as on the distance and the orientation from where this object is observed.
Solid Angle of a surface is, by definition, equal to the projected spherical surface in the evolving sphere divided by the square of the radius of the sphere. As an aproximation, we use the ellipse surface area in place of the projected spherical surface in the evolving sphere. The maxSolidAngle map shows the value of the maximum Solid Angle among those measured from the different viewpoints. In this map, the closest pixels to the observation points have to be interpreted with special attention, considering that the error, respect to the real Solid Angle, can reach until the 10% in the immediate neighbor pixels
<p>
Other three maps (pointOfViewWithMin3dDistance, pointOfViewWithMmaxAngle and pointOfViewWithMmaxSolidAngle) are used to register, in each cell, the identifier of the viewpoints from where an observer can get, respectively, (i) the minimum values of 3D Distance, (ii) the maximum values of View Angle and (iii) the maximum value of the Solid Angle. Another relevant output is the numberOfViews map which portraits the number of viewpoints from where each pixel is visible.

<h2>INSTALLATION</h2>
<h3>LINUX:</h3>

1) Download the compressed folder of r.survey from <a href="https://doi.org/10.5281/zenodo.3993140">https://doi.org/10.5281/zenodo.3993140</a> and decompress it. 
<p>
2) Copy the file <em>r.survey.py</em> into the folder <em>/usr/lib/grass78/scripts/</em>
<p> 
3) Copy the file <em>r.survey.html</em> and the folder <em>r.survey_figures</em> into the directory <em>/usr/lib/grass78/docs/html/</em>
<p> 
4) Open GRASS and run the following commands in order to verify if it works: 
<dd><div class="code"><pre>r.survey --h</pre></div></dd>
<dd><div class="code"><pre>g.manual r.survey</pre></div></dd>

<h3>WINDOWS:</h3>

Depending on the type of GRASS installation carried out, the directory paths can slightly vary. 
<p>
1) Download the compressed folder of r.survey from <a href="https://doi.org/10.5281/zenodo.3993140">https://doi.org/10.5281/zenodo.3993140</a> and decompress it. 
<p>
2) Copy the file named <em>r.survey.bat</em> into the following directory:

<dd><em>C:\Program Files\GRASS GIS 7.8\bin\</em>  (regular installation)</dd>
<dd>or</dd>
<dd><em>C:\OSGeo4W64\apps\grass\grass78\bin\</em> (installation from OSGeo)</dd>
<p>
3) Copy the file <em>r.survey.py</em> into the followin folder:

<dd><em>C:\Program Files\GRASS GIS 7.8\scripts\</em>  (regular installation)</dd>
<dd>or</dd>
<dd><em>C:\OSGeo4W64\apps\grass\grass78\scripts\</em> (installation from OSGeo)</dd>
<p>
4) Copy the file <em>r.survey.html</em> and the folder <em>r.survey_figures</em> into the following directory:

<dd><em>C:\Program Files\GRASS GIS 7.8\docs\html\</em>  (regular installation)</dd>
<dd>or</dd>
<dd><em>C:\OSGeo4W64\apps\grass\grass78\docs\html\</em> (installation from OSGeo)</dd>
<p>

5) Open GRASS and run the following commands in order to verify if it works: 
<dd><div class="code"><pre>r.survey --h</pre></div></dd>
<dd><div class="code"><pre>g.manual r.survey</pre></div></dd>

<h2>NOTES</h2>
The software was designed as a GRASS GIS python module whose source code was  written using the GRASS Scripting library and the pyGRASS library.
<p>
Multi-core processing is used by r.survey for reducing the computational time. When the aim is to derive the values of the visibility indexes along a given path (e.g. a road or a UAV track) viewpoints can be very dense in terms of number per unit of distance and the more the viewpoints are,  the longer the computational time becomes.  
<p>
Parallel computation was implemented exploiting the Python Multiprocessing library and the ability of GRASS GIS to set a temporary spatial region centered on the considered point without affecting the parallel computation of the other points.


<h2>EXAMPLES</h2>
The location used for the following examples can be downloaded from this folder. The name is R.SURVEY_Location
<p>
1) The most common usage of this tool is to model the visivility from the roads, for which a set of points located along the roads is needed. We are going to create a sample of points each 50 meters along the road.

<br>
<div class="code"><pre>
g.region raster=dem 
v.build.polylines input=roads output=roads_poly cats=multi  # Convert the road layer into polyline
v.to.points input=roads_poly output=points_50 dmax=50  # A point is created each 50 meters

v.category input=points_50 output=points_50_del option=del cat=-1 # Ensure that each point has an independent category value
v.category input=points_50_del output=points_50_add option=add cat=1 # Ensure that each point has an independent category value
</pre></div>
<p>
2) This example shows how to run r.survey calculating the solid angle for an object of radius equal to 20 m and using 4 parallel processes. The height of a tower is considered as well into the calculations. 

<br>
<div class="code"><pre>
g.region raster=Synthetic_valley 
r.survey points=Two_viewpoints dem=Synthetic_valley output=example maxdist=3000 buildingsmap=Tower buildingsheigh=Altitude object_radius=20 nprocs=4
</pre></div>
<p>
3) This example shows how to run r.survey calculating the same layers as in example 1, but this time the outputs are filtered by a View Angle threshold of 100 degrees.

<br>
<div class="code"><pre>
g.region raster=Synthetic_valley 
r.survey points=Two_viewpoints dem=Synthetic_valley output=example2 maxdist=3000 buildingsmap=Tower buildingsheigh=Altitude object_radius=20 nprocs=4 viewangle_threshold=100
</pre></div>
<p>
4) This example shows how to run r.survey in flight mode and with the downward view. The observation points correspond for the path of an UAV flying in a irregular height above the ground. A field with the points altitude information (above de sea level) is mandatory.

<br>
<div class="code"><pre>
g.region raster=Synthetic_valley 
r.survey -d points=Flight_viewpoints dem=Synthetic_valley output=example3 maxdist=3000 nprocs=4 obsabselev=Elevation
</pre></div>

<h2><a name="references">REFERENCES</a></h2>
<ul>
<li>Bornaetxea, T., Marchesini, I. <i>r.survey: a tool for calculating visibility of variable-size objects based on orientation</i>,<b>International Journal of Geographical Information Science</b>, <a href="https://www.tandfonline.com/doi/full/10.1080/13658816.2021.1942476">https://www.tandfonline.com/doi/full/10.1080/13658816.2021.1942476</a>

</ul>

<h2><a name="see-also">SEE ALSO</a></h2>

<em>
<a href="r.viewshed.html">r.viewshed</a>
</em>

<h2><a name="authors">AUTHORS</a></h2>

Ivan Marchesini - Research Institute for Geo-Hydrological Protection (IRPI) - Italian National Research Council (CNR), Perugia, Italy. E-mail: ivan.marchesini@irpi.cnr.it. ORCiD: 0000-0002-8342-3134
<br>
Txomin Bornaetxea - Department of Geology, University of the Basque Country (UPV/EHU), Leioa, Spain. E-mail: txomin.bornaetxea@ehu.eus. ORCiD: 0000-0002-1540-3991



</div>
</body>
</html>
