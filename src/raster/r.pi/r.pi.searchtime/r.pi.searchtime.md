## DESCRIPTION

Individual-based dispersal model for connectivity analysis (time-based)

This module provides information about the isolation or connectivity of
individual fragments derived of a landcover classification. Unlike
*r.pi.energy* this module provides information about the time from
emigration to immigration. The individual based dispersal model results
are based on the step length and range, the perception distance and the
attractivity to move towards patches.

## NOTES

The suitability matrix impacts the step direction of individuals. If
individuals are moving beyond the mapset borders the indivuals are set
back to their original source patches.

## EXAMPLE

An example for the North Carolina sample dataset:

The connectivity of patches of the *landclass96* class 5 are computed
using the time from emigration to immigration. The step length is set to
5 pixel, the output statistics are set to *average* time and *variance*
of searchtime. For each patch 1000 individuals were released and the
model stopped when at least 80% of all individuals sucessfully
immigrated:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000
```

constrain the angle of forward movement to 10 degrees:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 step_range=10
```

setting the perception range to 10 pixel:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 perception=10
```

increasing the attraction to move towards patches to 10:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 multiplicator=10
```

limiting the amount of steps to 10:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 maxsteps=10
```

output of each movement location for a defined step frequency. Here
every 10th step is provided as output raster:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 out_freq=10
```

output of a raster which immigration counts:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 out_immi=immi_counts
```

output of a binary immigration matrix. Each patch emigration and
immigration for all patch combinations is recorded as 0 or 1:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 binary_matrix=binary_matrix.txt
```

output of a matrix with immigration counts for each patch:

```sh
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 immi_matrix=immi_counts.txt
```

the previous examples assumed a homogeneous matrix, a heterogenous
matrix can be included using a raster file which values are taken as
costs for movement (0-100):

```sh
# it is assumed that our species is a forest species and cannot move
# through water, hence a cost of 100, does not like urban areas
# (class: 6, cost: 10) but can disperse through shrubland (class 4,
# cost=1) better than through grassland (class 3, cost: 2):

r.mapcalc "suit_raster = if(landclass96==5,1,if(landclass96 == 1, 10, if (landclass96==3,2, if(landclass96==4,1,if(landclass96==6,100)))))"
r.pi.searchtime input=landclass96 output=searchtime1 keyval=5 step_length=5 stats=average,variance percent=80 n=1000 suitability=suit_raster
```

## SEE ALSO

*[r.pi.searchtime.pr](r.pi.searchtime.pr.md),
[r.pi.searchtime.mw](r.pi.searchtime.mw.md), [r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
