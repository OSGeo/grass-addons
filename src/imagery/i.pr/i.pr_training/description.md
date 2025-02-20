## NAME

***i.pr.training*** - Module to generate the training samples for use in
i.pr.\* modules. i.pr: Pattern Recognition environment for image
processing. Includes *k*NN, Decision Tree and SVM classification
techniques. Also includes cross-validation and bagging methods for model
validation.

## SYNOPSIS

**i.pr.training** **i.pr.training** **map**=*string*\[,*string*,...\]
\[**vis\_map**=*string*\] **training**=*string*
\[**site\_file**=*string*\] **rows**=*value* **cols**=*value*
\[**class**=*value*\] \[**--verbose**\] \[**--quiet**\]

### Flags:

**Flags:**

\--v Verbose module output

\--q Quiet module output

### Parameters:

  - **input**=*string\[,*string*,...\]*  
    Input raster maps (max 25) for extracting the training examples. The
    first one will be used for graphical output, where 'vis\_map' is
    specified
  - **vis\_map**=*string*  
    Raster Map for visualisation
  - **training**=*string*  
    Name of the output file containing the training raster maps. If this
    file already exists, the new data will be appended to the end of the
    file.
  - **site\_file**=*string*  
    Name of the site file containing the labelled location. Typically a
    point vector layer or polygon centroids
  - **rows**=*value*  
    Number of rows (required odd) of the training samples
  - **cols**=*value*  
    Number of columns (required odd) of the training samples
  - **class**=*value*  
    Numerical label to be attached to the training examples. Option not
    required with the site\_file option.

## DESCRIPTION

*i.pr.training* This module is the first to be run when using i.pr.\*
modules. It is necessary to list all maps that will be used as
explanatory variables and whose values will be assigned to the training
samples. Two options for extracting data for the training samples are
available. The first can be done interactively using the graphical
interface. In this instance, the first GRASS raster map specified in the
list is visualised in the GRASS monitor, however, this can be altered by
specifying the 'vis\_map' option. In this case, the user must digitise
locations training samples in the GRASS monitor. A Class parameter will
be assigned to each training sample, the class labels must be positive
integers and must progressively increase. The second option for
generating the training sample file can be done non-interactively. This
is done by specifying a GRASS sites file. This file should represent the
locations of training samples and ought to have been previously
generated either by digitising
(*[v.digit](https://grass.osgeo.org/grass-stable/manuals/v.digit.html)*)
or else by
*[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html)*.
Features will be extracted for these locations in a similar fashion as
previously described. The class will be assigned to the examples based
on the information stored in the sites file.

The output of this module will be an ascii file of type xy.z. The number
of columns will relate to the number of rasters specified on the command
line. If the output file already exists, the new data values will be
appended to it.

### Flags:

**--v** Verbose module output. Print information pertaining to module
progress and completion.

**--p** Run Quietly. Suppress program output that would include program
percent complete messages and time elapsed.

### Parameters:

**input=***name,name*\[*,name,name*,...\]

Name of raster maps (maximum 25) for extracting the training examples.
The first will be used for graphical output. The extent of all raster
maps should be the same. CELL, DCELL and FCELL raster maps can be used.

**vis\_map***name*

This parameter is optional. If used, the raster that is specified will
be displayed in the GRASS monitor and used as a background raster file.
It should be used to identify the location of training samples.

**training=***name*

This parameter is required. It creates the training file, which is an
ascii file containing all of the x,y locations of the traning samples
and their associated class labels and values from the explanatory
variables (GRASS raster maps). If the name specified on the command line
refers to a training file that already exists in the working directory,
the new data are appended to it.

**site\_file=***name*

This parameter is required if the non-interactive mode is required. It
should relate to a GRASS Vector map (Version 6 vector data) and there
should be a class label (numeric value) for each site. This file should
be created prior to running i.pr.training either using v.digit or
v.in.ascii. The latter is more straightforward provided the input ascii
file contains data in the following format: x,y,z(class label).

**rows=***value*

The number of rows in the training samples, this must be odd.

**cols=***value*

The number of colums in the training samples, this must be odd.

**class=***value*

The numerical label to be attached to the training examples. This is
only required when the interactive mode of i.pr.training is used.

## NOTES

## SEE ALSO

*[i.pr\_features](i.pr_features.md)*  

## AUTHORS

Stefano Merler, FBK, Trento, Italy  
Documentation: Daniel McInerney (daniel.mcinerney ucd.ie)
