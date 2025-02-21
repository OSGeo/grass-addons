## DESCRIPTION

Determine the functional nearest-neighbor distance analysis. *r.pi.fnn*
is a patch based ecological/functional nearest neighbour analysis
module. It computes distance based on a friction map. This module is
related to *r.pi.enn* but more adequate if the ecological connectivity
should be analysed.

## NOTES

The calculation of the ecolgogical nearest neighbour is based on a
raster with start patches. The actual map can be categorical or
continuous but the value defined in *keyval* will be the basis for the
patches to calculate the methods defined below. These patches will also
be in the output map. The calculation of the ecolgogical nearest
neighbour is based on a costmap (\* and 1-infinite) - this map can be
binary or continous - high values are considered to have high cost
issues and the shortest path is the one with the lowest amount of costs.
"null" values can not be traversed, hence these values have to be
bypassed. "0" values are not accepted and will result in "0" distance.

e.g. if a binary map(1 and 2) is used, the the path with the lowest
amount of "1" is chosen The *number* is the amount of nearest neighbours
to be taken and the calculated distances are processed as assigned in
*statmethod* Operations which *r.pi.fnn* can perform are:

- **Distance**  
    The *Distance to Nearest* computes the nearest edge-to-edge distance
    between patches. Counting from the focus patch.
- **path Distance**  
    The *Distance to Nearest* computes the nearest edge-to-edge distance
    between patches. Unlike *Distance* the distance is computed based on
    subsequent NN not from the focus patch onwards. The 1th NN is the
    first patch with the minimal edge-to-edge distance from the focus
    patch, while 2th NN is the patch with the minimal edge-to-edge
    distance from the 1th NN patch and so on.
- **Area**  
    The *Area* computes the size of the nearest edge-to-edge distance
    patch. It is based on *Distance* not on *path Distance*.
- **Perimeter**  
    The *Perimeter* computes the Perimeter of the nearest edge-to-edge
    distance patch. It is based on *Distance* not on *path Distance*.
- **SHAPE**  
    The *SHAPE* computes the SHAPE Index of the nearest edge-to-edge
    distance patch. It is based on *Distance* not on *path Distance*.

The *statsmethod* operators determine calculation is done on the
distance. *Average*, *Variance*,*Stddev* and *value* can be used.

- **Average**  
    The *Average* computes the average value defined in *Operations to
    perform* .
- **Variance**  
    The *Variance* computes the variance defined in *Operations to
    perform* .
- **Stand. Dev.**  
    The *Stand. Dev.* computes the stddev value defined in *Operations
    to perform* .
- **Value**  
    The *patch Distance* computes the nearest edge-to-edge distance
    between two patches. The output of *value* is the actual value. E.g.
    NN==5 of *area* gives the size of the 5th NN while *Average* gives
    the average of the area of 1-5th NN.

The input options are either one NN: *1* or several NN separated by *,*:
1,2,5,8 or a range of NN: 1-6.

Merging these options is possible as well: 1-5,8,9,13,15-19,22 etc.

## EXAMPLE

An example for the North Carolina sample dataset: Computing the
functional or ecological distance to the first to nth nearest
neighrbours using a cost matrix:

```sh
r.mapcalc "cost_raster = if(landclass96==5,1,if(landclass96 == 1, 10, if (landclass96==3,2, if(landclass96==4,1,if(landclass96==6,100)))))"
r.pi.fnn input=landclass96 keyval=5 costmap=cost_raster output=fnn1 method=distance number=10 statmethod=average
```

## SEE ALSO

*[r.pi.enn](r.pi.enn.md), [r.pi.index](r.pi.index.md), [r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
