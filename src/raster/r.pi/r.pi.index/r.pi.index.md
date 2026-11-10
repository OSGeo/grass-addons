## DESCRIPTION

*r.pi.index* is a patch based fragmentation analysis package.
Computation of basic fragmentation indices can be accomplished.

Available options for the index to be computed for patches within a
certain class are: area (area), perimeter (perim), SHAPE (shape),
Border-Index (bor), Compactness (comp), Asymmetry (asym), area-perimeter
ratio (apr), fractal dimension (fract), distance to euclidean nearest
neighbour (ENN).

## NOTES

The *Nearest Neighbour Index* (ENN) analyse the Euclidean Nearest
Neighbour to the first neighbouring patch. The output value is in pixel
and can be converted to a distance values using g.region resolution
information. *r.pi.enn* and *r.pi.fnn* provide the same analysis
concerning the first nearest neighbour (NN), but are extended to the
n-th NN. However due to code construction does the *r.pi.index* distance
analysis to first ENN perform faster. *Methods:* The *method* operators
determine what algorithm is applied on the patches. *r.pi.index* can
perform the following operations:

- **Area**  
    The *Area* computes the area of each patch.
- **Perimeter**  
    The *Perimeter* computes the perimeter of each patch.
- **Area-Perimeter ratio**  
    The *Area-Perimeter ratio* divides the patch perimeter by the area.
- **SHAPE Index**  
    The *SHAPE Index* divides the patch perimete by the minimum
    perimeter possible for a maximally compact patch of the
    corresponding patch area.
- **Border Index**  
    The *Border Index* ....
- **Compactness Index**  
    The *Compactness Index* ....
- **Asymmetry Index**  
    The *Border Index* ....
- **Fractal Dimension Index**  
    The *Fractal Dimension Index* ....
- **Nearest Neighbour Index**  
    The *Nearest Neighbour Index* computes the Euclidean distance to the
    first nearest neighbour patch.

## EXAMPLE

Examples based on the North Carolina sample dataset are provided below.
Indices are calculated for the landscape class 5 (forest). set region
settings to used landcover class map:  

```sh
g.region rast=landclass96
```

computation of patch size (patch definition: 4-neighbourhood rule)

```sh
r.pi.index input=landclass96 output=landclass96_forestclass5_area keyval=5 method=area
# improve colouring of resulting map:
r.colors landclass96_forestclass5_area col=bgyr
```

computation of patch size (patch definition: 8-neighbourhood rule)

```sh
r.pi.index input=landclass96 output=landclass96_forestclass5_area keyval=5 method=area -a
```

computation of patch isolation (euclidean distance to 1. nearest
neighbour; patch definition: 4-neighbourhood rule)

```sh
r.pi.index input=landclass96 output=landclass96_forestclass5_ENN keyval=5 method=ENN -a
```

## SEE ALSO

*[r.pi.enn](r.pi.enn.md), [r.pi.import](r.pi.import.md),
[r.pi.rectangle](r.pi.rectangle.md), [r.pi](r.pi.md)*

## BUGS

Landscapes with more than 10 000 individual patches might cause a memory
allocation error depending on the user's system.

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
