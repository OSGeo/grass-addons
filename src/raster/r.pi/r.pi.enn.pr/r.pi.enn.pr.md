## DESCRIPTION

Patch relevance for Euclidean Nearest Neighbor patches.

*r.pi.enn.pr* computes distance and area differences for the first NN
after removal of patch i.

## NOTES

The *keyval* operator determines which category value is taken for the
Patch Index analysis.

The *method* operators determine what measure is applied on the nth NN
(area or distance).

Differences of distance/area after removal of patch i are provided as
output as well as the amount of patches to be affected by its removal
(percent) (PP) and the amount of area in these patches (PA - Percent
Area)

## EXAMPLE

An example for the North Carolina sample dataset:

Analysing the differences (average) in distance when patch i of class 5
is removed:

```sh
r.pi.enn.pr input=landclass96 output=dist_iter keyval=5 method=distance statmethod=average
```

## SEE ALSO

*[r.pi.index](r.pi.index.md), [r.pi.enn](r.pi.enn.md),
[r.pi.fnn](r.pi.fnn.md), [r.pi.searchtime.pr](r.pi.searchtime.pr.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
