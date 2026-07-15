## DESCRIPTION

*i.pr.features* This module is used to preprocess and extract the
training features. It is necessary to specify the training file, which
contains the names of the raster maps (explanatory variables) to be used
in subsequent modules. The training file can either be the output from
from *[i.pr.training](i.pr.training.md)* (Recommended) or an ascii file
containing the names of rasters.

This module allows for the calculation of a range of statistics
pertaining to the explanatory variables, which include the mean and
variance. In addition the features can be normalized to a similar scale.
In each case, it is possible to specify the numbers of features for
which these statistics should be computed (i.e. number in list). There
is also the possibility to compute principal components for the
explanatory variables. The default calculates them for all layers, or
else only on selected classes specified by 'class\_pc'. Variables can be
standardised using parameter 'standardize', this is linked to the
features previously calculated and not layers in the training file.

## NOTES

## SEE ALSO

*[i.pr.training](i.pr.training.md)*  
*[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html)*  

## AUTHORS

Stefano Merler, FBK, Trento, Italy  
Documentation: Daniel McInerney (daniel.mcinerney ucd.ie)
