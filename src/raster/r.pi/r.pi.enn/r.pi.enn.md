## DESCRIPTION

*r.pi.enn* computes the euclidean distance between patches (1-n NN).
Analysis of n-th euclidean nearest neighbour distance.

## NOTES

The user must specify the names of the raster map layers to be used for
*input* and *output*, the *keyval* the *method* (e.g. distance, area)
and *statmethod* used (i.e., average).

Within *r.pi.enn* the following setting have to be set:

### keyval setting:

The *keyval* operator determines which category value is taken for the
Patch Index analysis.

### Method setting:

The *method* operators determine what measure is applied on the nth NN.

- **Distance**  
    The *Average* computes the average distance of the n NN.
- **Path distance**  
    The *path\_distance* computes the actual distance to the n NN.
- **Area**  
    The *area* computes the area of the n NN.
- **Perimeter**  
    The *perimeter* computes the perimeter of the n NN.
- **SHAPE Index**  
    The *shapeindex* computes the SHAPE Index of the n NN.

### Statmethod setting:

The *statmethod* operators determine what statistic measure is applied
on the nth NN.

- **Average**  
    The *Average* computes the average distance of the n NN.
- **Variance**  
    The *Variance* computes the variance of the distance of the n NN.
- **Std. Dev.**  
    The *Std. Dev* computes the std. dev. of the distance of the n NN.

### Number:

The *keyval* operator determines which or how many Nearest Neighbour are
analysed. *1,2,5* will analyse the 1, 2 and 5th Nearest Neigbour. *1-10*
will analyse the 1, 2, 3, ... 10th Nearest Neighbour. *0* will analyse
all Nearest Neighbours.

### Distancematrix:

The *dmout* operator is optional and determines if a distance matrix is
written (first NN only). *1,2,5* will analyse the 1, 2 and 5th Nearest
Neigbour. *1-10* will analyse the 1, 2, 3, ... 10th Nearest Neighbour.
*0* will analyse all Nearest Neighbours.

## EXAMPLE

An example for the North Carolina sample dataset:

```sh
r.pi.enn input=landclass96 output=dist1.c5 keyval=5 method=distance number=1 statmethod=average
# -> gives a map of patches (all of category of 5) with the average distance to their first NN

r.pi.enn input=landclass96 output=dist10.c5 keyval=5 method=distance number=10 statmethod=average
# -> gives a map of patches (all of category of 5) with the average distance to their first-10th NN

r.pi.enn input=landclass96 output=dist1.5.10.c5 keyval=5 method=distance number=1,5,10 statmethod=average
# -> gives a map of patches (all of category of 5) with the average distance to their first, first-to-fifth and first-to-10th NN

r.pi.enn input=landclass96 output=dist10b.c5 keyval=5 method=path_distance number=10 statmethod=average
# -> gives a map of patches (all of category of 5) with the actual distance to the 10th NN
```

## SEE ALSO

*[r.pi.index](r.pi.index.md), [r.fragment.dist](r.fragment.dist.md),
[r.pi.enn](r.pi.enn.md), [r.pi.enn.pr](r.pi.enn.pr.md),
[r.fragment.neighbors](r.fragment.neighbors.md),
[r.li](https://grass.osgeo.org/grass-stable/manuals/r.li.setup.html)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
