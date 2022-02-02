<h2>DESCRIPTION</h2>

<em>r.shaded.pca</em> is a tool for the generation
of RGB composite of the three main components
of PCA created from different hill shades
(created by <em><a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a></em>).

<h3>Input parameters explanation</h3>

Input parameters are the same as for
<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a></em> module except for
an <i>azimuth</i> parameter which is replaced by <i>nazimuths</i> parameter
(we need to specify number of different azimuths rather than one)
and for an <i>nprocs</i> parameter which adds the possibility to run the
shades creation (<em><a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a></em>)
in parallel. However, the speed of <em><a href="https://grass.osgeo.org/grass-stable/manuals/i.pca.html">i.pca</a></em>
limits the overall speed of this module.

In order to provide simple interface, it is not possible to customize
principal component analyses which uses the default settings of the
<em><a href="https://grass.osgeo.org/grass-stable/manuals/i.pca.html">i.pca</a></em> module.

<h3>Output parameters explanation</h3>

The the standard output map is an RGB composition of first three principal
components where components are assigned to red, green and blue colors
in this order.

If you want to create your own RGB composition, HIS composition or do another
analyses you can specify the <i>pca_shades_basename</i> parameter. If this
parameter is specified, the module outputs the PCA maps as created during
the process by <em><a href="https://grass.osgeo.org/grass-stable/manuals/i.pca.html">i.pca</a></em>.

Moreover, if you would like to add one of the shades to your composition,
you can specify the <i>shades_basename</i> parameter then the module will
output also the hill shade maps as created during
the process by <em><a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a></em>.
One of the shades can be used to subtract the intensity channel in HIS
composition or just as an overlay in your visualization tool.

<h2>EXAMPLE</h2>

<div class="code"><pre>
# basic example with changed vertical exaggeration
r.shaded.pca input=elevation output=elevation_pca_shaded zscale=100

# example of more complicated settings
# including output shades and principal component maps
r.shaded.pca input=elevation output=elevation_pca_shaded \
 zscale=100 altitude=15  nazimuths=16 nprocs=4 \
 shades_basename=elevation_pca_shaded_shades pca_shades_basename=elevation_pca_shaded_pcs
</pre></div>

<!--
region used for image unknown but something like is ok:
g.region n=228010 s=223380 w=637980 e=644920 res=10
default settings used
-->
<center>
<img src="r.shaded.pca.png" alt="3 PCA RGB composition">
<p>
Figure: The RGB composition of first 3 PCA components
(output from <em>r.shaded.pca</em> with default values)
</center>

<h2>SEE ALSO</h2>

<em>
<a href="https://grass.osgeo.org/grass-stable/manuals/r.relief.html">r.relief</a>,
<a href="https://grass.osgeo.org/grass-stable/manuals/i.pca.html">i.pca</a>,
<a href="r.local.relief.html">r.local.relief</a>,
<a href="r.skyview.html">r.skyview</a>
</em>

<h2>REFERENCES</h2>

Devereux, B. J., Amable, G. S., & Crow, P. P. (2008). Visualisation of LiDAR terrain models for archaeological feature detection. Antiquity, 82(316), 470-479.

<h2>AUTHOR</h2>

Vaclav Petras, <a href="http://gis.ncsu.edu/osgeorel/">NCSU OSGeoREL</a>
