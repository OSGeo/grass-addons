<h2>NAME</h2>
<em><b>i.pr.training</b></em>  - Module to generate the training samples for use in i.pr.* modules. i.pr: Pattern Recognition environment for image processing. Includes <i>k</i>NN, Decision Tree and SVM classification techniques. Also includes cross-validation and bagging methods for model validation.
<h2>SYNOPSIS</h2>
<b>i.pr.training</b>
<b>i.pr.training</b> <b>map</b>=<em>string</em>[,<i>string</i>,...] [<b>vis_map</b>=<em>string</em>]  <b>training</b>=<em>string</em> [<b>site_file</b>=<em>string</em>] <b>rows</b>=<em>value</em> <b>cols</b>=<em>value</em> [<b>class</b>=<em>value</em>] [<b>--verbose</b>] [<b>--quiet</b>]


<h3>Flags:</h3>
<dl>
<dd><b>Flags:</b></dd>
<dd>--v	Verbose module output</dd>
<dd>--q Quiet module output</dd>
</dl>

<h3>Parameters:</h3>
<dl>
<dt><b>input</b>=<em>string[,<i>string</i>,...]</em>
<dd>Input raster maps (max 25) for extracting the training examples. The first one will be used for graphical output, where 'vis_map' is specified</dd>

<dt><b>vis_map</b>=<em>string</em>
<dd>Raster Map for visualisation</dd>

<dt><b>training</b>=<em>string</em>
<dd>Name of the output file containing the training raster maps. If this file already exists, the new data will be appended to the end of the file.<dd>

<dt><b>site_file</b>=<em>string</em>
<dd>Name of the site file containing the labelled location. Typically a point vector layer or polygon centroids</dd>

<dt><b>rows</b>=<em>value</em>
<dd>Number of rows (required odd) of the training samples</dd>

<dt><b>cols</b>=<em>value</em>
<dd>Number of columns (required odd) of the training samples</dd>

<dt><b>class</b>=<em>value</em>
<dd>Numerical label to be attached to the training examples. Option not required with the site_file option.</dd>
</dl>
<h2>DESCRIPTION</h2>


<em>i.pr.training</em> This module is the first to be run when using i.pr.* modules. It is necessary to list all maps that will be used as explanatory variables and whose values will be assigned to the training samples. Two options for extracting data for the training samples are available. The first can be done interactively using the graphical interface. In this instance, the first GRASS raster map specified in the list is visualised in the GRASS monitor, however, this can be altered by specifying the 'vis_map' option. In this case, the user must digitise locations training samples in the GRASS monitor. A Class parameter will be assigned to each training sample, the class labels must be positive integers and must progressively increase.
<pr>
The second option for generating the training sample file can be done non-interactively. This is done by specifying a GRASS sites file. This file should represent the locations of training samples and ought to have been previously generated either by digitising (<em><a href="https://grass.osgeo.org/grass-stable/manuals/v.digit.html">v.digit</a></em>) or else by <em><a href="https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html">v.in.ascii</a></em>. Features will be extracted for these locations in a similar fashion as previously described. The class will be assigned to the examples based on the information stored in the sites file.
<p>
The output of this module will be an ascii file of type xy.z. The number of columns will relate to the number of rasters specified on the command line. If the output file already exists, the new data values will be appended to it.

<h3>Flags:</h3>
<dl>
<dd><b>--v</b>	Verbose module output. Print information pertaining to module progress and completion.</dd>
<dd><b>--p</b>	Run Quietly. Suppress program output that would include program percent complete messages and time elapsed.</dd>
<h3>Parameters:</h3>


<dt><b>input=</b><em>name,name</em>[<em>,name,name</em>,...]</dt>
<dd>Name of raster maps (maximum 25) for extracting the training examples. The first will be used for graphical output. The extent of all raster maps should be the same. CELL, DCELL and FCELL raster maps can be used. </dd>


<dt><b>vis_map</b><em>name</em>
<dd>This parameter is optional. If used, the raster that is specified will be displayed in the GRASS monitor and used as a background raster file. It should be used to identify the location of training samples.</dd>

<dt><b>training=</b><em>name</em>
<dd>This parameter is required. It creates the training file, which is an ascii file containing all of the x,y locations of the traning samples and their associated class labels and values from the explanatory variables (GRASS raster maps). If the name specified on the command line refers to a training file that already exists in the working directory, the new data are appended to it. </dd>

<dt><b>site_file=</b><em>name</em>
<dd>This parameter is required if the non-interactive mode is required. It should relate to a GRASS Vector map (Version 6 vector data) and there should be a class label (numeric value) for each site. This file should be created prior to running i.pr.training either using v.digit or v.in.ascii. The latter is more straightforward provided the input ascii file contains data in the following format: x,y,z(class label).
</dd>

<dt><b>rows=</b><em>value</em>
<dd>The number of rows in the training samples, this must be odd.</dd>
<dt><b>cols=</b><em>value</em>
<dd>The number of colums in the training samples, this must be odd.</dd>

<dt><b>class=</b><em>value</em>
<dd>The numerical label to be attached to the training examples. This is only required when the interactive mode of i.pr.training is used. </dd>

<h2>NOTES</h2>


<h2>SEE ALSO</h2>

<em><a href="i.pr_features.html">i.pr_features</a></em><br>

<h2>AUTHORS</h2>

Stefano Merler, FBK, Trento, Italy<br>
Documentation: Daniel McInerney (daniel.mcinerney ucd.ie)
