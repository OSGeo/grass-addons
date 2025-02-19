<h2>DESCRIPTION</h2>

<em>r.terrain.texture</em> calculates the nested-means terrain classification of Iwahashi and Pike (2007). This classification procedure relies on three surface-form metrics consisting of: (a) terrain surface texture which is represented by the spatial frequency of peaks and pits; (b) surface-form convexity and concavity which are represented by the spatial frequency of convex/concave locations; and (c) slope-gradient which should be supplied by <em>r.slope.aspect</em> or <em>r.param.scale</em>. These metrics are combined using the mean of each variable as a dividing measure into a 8, 12 or 16 category classification of the topography.

<p>
The calculation follows the description in Iwahashi and Pike (2007). Terrain surface texture is calculated by smoothing the input <i>elevation</i> using a median filter over a neighborhood specified by the <i>filter_size</i> parameter (in pixels). Second, pits and peaks are extracted based on the difference between the smoothed DEM and the original terrain surface. By default the algorithm uses a threshold of 1 (&gt; 1 m elevation difference) to identify pits and peaks. This threshold is set in the <i>flat_thres</i> parameter. The spatial frequency of pits and peaks is then calculated using a Gaussian resampling filter over a neighborhood size specified in the <i>counting_filter</i> parameter (default is 21 x 21 pixels, as per Iwahashi and Pike (2007).
</p>

<p>
Surface-form convexity and concavity are calculated by first using a Laplacian filter approximating the second derivative of elevation to measure surface curvature. The Laplacian filter neighborhood size is set by the <i>filter_size</i> parameter (in pixels). This yields positive values in convex-upward areas, and negative values in concave areas, and zero on planar areas. Pixels are identified as either convex or concave when their values exceed the <i>curv_thres</i>. Similarly to terrain surface texture, the spatial frequency of these locations is then calculated to yield terrain surface convexity and concavity measures.
</p>

<p>
Optionally, these surface-form metrics along with slope-gradient can be used to produce a nested-means classification of the topography. Each class is estimated based on whether the pixels values for each variable exceed the mean of that variable. The classification sequence follows:</p>

<center>
<img src="flowchart.png" alt="Terrain classification flowchart">
</center>

<p>A single iteration of this decision tree is completed for the 8-category classification. However for the 12 category classification, classes 1-4 remain but pixels that otherwise relate to classes 5-8 are passed to a second iteration of the decision tree, except that the mean of the gentler half of the area is used as the decision threshold, to produce 8 additional classes. Similarly for the 16 category classification, pixels that otherwise relate to classes 8-12 are passed onto a third iteration of the decision tree, except that the mean of the gentler quarter of the area is used as the decision threshold. This iterative subdivision of terrain properties acts to progressively partition the terrain into more gentle terrain features.</p>

<h2>NOTES</h2>
In the original algorithm description, SRTM data was smoothed using a fixed 3 x 3 size median filter and the spatial frequency of extracted features were measured over a 21 x 21 sized counting window. However, a larger smoothing filter size (~15 x 15) is often required to extract meaningful terrain features from higher resolution topographic data such as derived from LiDAR, and therefore both <i>filter_size</i> and <i>counting_size</i> parameters were exposed in the GRASS implementation. Further, if a large filter size is used then the counting window size should be increased accordingly.

<h2>EXAMPLE</h2>

<p>Here we are going to use the GRASS GIS sample North Carolina data set as a basis to perform a terrain classification. First we set the computational region to the elev_state_500m dem, and then generate shaded relief (for visualization) and slope-gradient maps:</p>

<div class="code"><pre>
g.region raster=elev_state_500m@PERMANENT
r.relief input=elev_state_500m@PERMANENT output=Hillshade_state_500m altitude=45 azimuth=315
r.slope.aspect elevation=elev_state_500m@PERMANENT slope=slope_state_500m
</pre></div>

<p>Then we produce the terrain classification:</p>

<div class="code"><pre>
r.terrain.texture elevation=elev_state_500m@PERMANENT slope=slope_state_500m@PERMANENT \
  texture=texture_state_500m convexity=convexity_state_500m concavity=concavity_state_500m \
  features=classification_state_500m
</pre></div>

<p>Terrain surface texture:</p>
<center>
<img src="texture_example.png" alt="Terrain surface texture result">
</center>

<p>Surface-form convexity:</p>
<center>
<img src="convexity_example.png" alt="Terrain convexity result">
</center>

<p>8-category terrain classification:</p>
<center>
<img src="classification_example.png" alt="8-category nested-means classification result">
</center>

<h2>REFERENCES</h2>

Iwahashi, J., and Pike, R.J. 2007. Automated classifications of topography
from DEMs by an unsupervised nested-means algorithm and a three-part geometric
signature. Geomorphology 86, 409-440.

<h2>AUTHOR</h2>

Steven Pawley
