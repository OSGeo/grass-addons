## DESCRIPTION

*r.pi.odc* is part of the patch based fragmentation analysis package
r.pi.\* (Patch Index). It computes omnidirectional connectivity analysis
between patches.

## NOTES

Several output raster are generated with the defined *output* file name
and a suffix of the information provided. All files named \*.FP.\* are
providing information concerning the focus patch. All files named
\*.TP.\* are providing informaton about the target patches.  
...

The user must specify the names of the raster map layers to be used for
*input* and *output*, the *keyval* the *ratio* (area/odd or odd/area)
and *stats* used (i.e., average).

Within *r.pi.odc* the following setting have to be set:

### keyval setting:

The *keyval* operator determines which category value is taken for the
Patch Index analysis.

### Ratio setting:

The *ratio* operators determine what measure is applied.

### Neighbourhood level:

The *neighbor\_level* operator determines which neighbourhood level is
used. *0* produces output for the focus patch itself, *1* assigns the
connectivity information of the first omnidirectional neighbours to the
focus patch, hence the connectivity of the surrouding fragments. This
value can be increased for analysing the more distant neighbours.

### Output:

Various output files are autmatically created with the pattern
$output.\* The ... *FP* describes attributes of the fokus patch (area
and area of the odd) *TP* describes attributes of the target patch (all
neighbouring patches around the FP) - separated by the statsmethod
(average, median, variance, stddev) *ratio* describes which ratio is
taken for all TPs. The output raster files are named accordingly:  
\*.FP.area: size of the patch  
\*.FP.odd: size of the isolation area  
\*.FP.odd\_area: ratio of size of patch and size of isolaton area  
\*.TP.no: amount of neighbouring patches  
\*.TP.area.avg: average size of all neighbouring patches  
\*.TP.odd.avg: average size of all isolation areas of neighbouring
patches  
\*.TP.odd\_area.avg: average ratio of isolation area to patch size  
\*.diagram: (if flag -d active) isolation areas and border are depicted

## EXAMPLE

An example for the North Carolina sample dataset:

```sh
r.pi.odc input=landclass96 output=odc keyval=5 ratio=odd_area stats=average neighbor_level=0 -d
```

## SEE ALSO

*[r.pi.fnn](r.pi.fnn.md), [r.pi.enn](r.pi.enn.md),
[r.pi.graph](r.pi.graph.md), [r.pi.index](r.pi.index.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
