## DESCRIPTION

Graph Theory for connectivity analysis.

## NOTES

...

## EXAMPLE

An example for the North Carolina sample dataset using class 5 (forest):
Computing a graph of all patches (4 neighbourhood rule) using a maximum
distance of 10 pixel, the Gabriel method and as resulting index the
*largest patch diameter*:

```sh
r.pi.graph input=landclass96 output=landclass96_graph keyval=5 distance=10 neighborhood=gabriel index=largest_patch_diameter
```

the results are 2 files:  
landclass96\_graph: the information of the index are provided (here a
range of 3-589 of patch diameter)  
landclass96\_graph\_clusters: the generated cluster IDs are provided
(here 16 clusters are identified), doing it with a distance of 5 pixel
is resulting in a total of 66 clusters.

## SEE ALSO

*[r.pi.corearea](r.pi.corearea.md), [r.pi.corr.mw](r.pi.corr.mw.md),
[r.pi.csr.mw](r.pi.csr.mw.md), [r.pi.export](r.pi.export.md),
[r.pi.graph.dec](r.pi.graph.dec.md), [r.pi.graph.pr](r.pi.graph.pr.md),
[r.pi.graph.red](r.pi.graph.red.md), [r.pi.grow](r.pi.grow.md),
[r.pi.import](r.pi.import.md), [r.pi.index](r.pi.index.md),
[r.pi.lm](r.pi.lm.md), [r.pi.odc](r.pi.odc.md),
[r.pi.prob.mw](r.pi.prob.mw.md), [r.pi.rectangle](r.pi.rectangle.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
