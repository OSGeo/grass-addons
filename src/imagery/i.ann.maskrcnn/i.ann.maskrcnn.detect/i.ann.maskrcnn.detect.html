<h2>DESCRIPTION</h2>

<em>i.ann.maskrcnn.detect</em> allows the user to use a Mask R-CNN model to
detect features in GRASS GIS raster maps or georeferenced files and extract
them either as areas or points. The module creates a separate map for each
class.

<h2>NOTES</h2>

<p>
The detection may be used for raster maps imported in GRASS GIS or for external
files (or using both). To use raster maps in GRASS GIS, you need to pass them
in three bands following the order used during the training, e.g. if the
training has been made on RGB images, use <em>band1=*.red</em>,
<em>band1=*.green</em> and <em>band3=*.blue</em>. To pass multiple images, put
more maps into <em>band*</em> parameters, divided by ",".

<p>
The detection may be used also for multiple external files. However, all files
for the detection must be in one directory specified in the
<em>images_directory</em> parameter. Even when using only one image, the module
finds it through this parameter.

<p>
When detecting, you can use new names of classes. Classes in the model are not
referenced by their name, but by their order. It means that if the model was
trained with classes <em>corn,rice</em> and you use
<em>i.ann.maskrcnn.detect</em> with classes <em>zea,oryza</em>, zea areas will
present areas detected as corn and oryza areas will present areas detected as
rice.

<p>
If the external file is georeferenced externally (by a worldfile or an
<em>.aux.xml</em> file), please use <em>-e</em> flag.

<h2>EXAMPLES</h2>

<h3>Detect buildings and lakes and import them as areas</h3>

<p>
One map imported in GRASS GIS:

<div class="code"><pre>
i.ann.maskrcnn.detect band1=map1.red band2=map1.green band3=map1.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5
</pre></div>

<p>
Two maps (map1, map2) imported in GRASS GIS:

<div class="code"><pre>
i.ann.maskrcnn.detect band1=map1.red,map2.red band2=map1.green,map2.green band3=map1.blue,map2.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5
</pre></div>

<p>
External files, the georeferencing is internal (GeoTIFF):

<div class="code"><pre>
i.ann.maskrcnn.detect images_directory=/home/user/Documents/georeferenced_images classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 images_format=tif
</pre></div>

<p>
External files, the georeferencing is external:

<div class="code"><pre>
i.ann.maskrcnn.detect images_directory=/home/user/Documents/georeferenced_images classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 images_format=png -e
</pre></div>

<h3>Detect cottages and plattenbaus and import them as points</h3>

<div class="code"><pre>
i.ann.maskrcnn.detect band1=map1.red band2=map1.green band3=map1.blue classes=buildings,lakes model=/home/user/Documents/logs/mask_rcnn_buildings_lakes_0100.h5 output_type=point
</pre></div>

<h2>SEE ALSO</h2>

<em>
<a href="i.ann.maskrcnn.html">Mask R-CNN in GRASS GIS</a>,
<a href="i.ann.maskrcnn.train.html">i.ann.maskrcnn.train</a>
</em>

<h2>AUTHOR</h2>

Ondrej Pesek
