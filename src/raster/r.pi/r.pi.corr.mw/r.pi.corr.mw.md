## DESCRIPTION

*r.pi.corr.mw* provides information concerning the correlation of pixels
inside a moving window between two raster files.

It calculates correlation of two raster maps by calculating correlation
function of two corresponding rectangular areas for each raster point
and writing the result into a new raster map.

## NOTES

This module computes the correlation between two raster files but unlike
*r.pi.lm* for moving windows of a specific size. This module is partly
based on *r.neighbors* and *r.covar*.

## EXAMPLE

An example for the North Carolina sample dataset: Correlation of all
pixels within a 7x7 sized window of two rasters (elevation and slope).
The output is multiplied by 10000 for higher precision

```sh
g.region rast=elevation -p
r.pi.corr.mw input1=slope input2=elevation output=corrwin1 size=7 max=10000
r.colors corrwin1 col=bgyr
```

## SEE ALSO

*[r.pi.index](r.pi.index.md), [r.pi.lm](r.pi.lm.md), [r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
