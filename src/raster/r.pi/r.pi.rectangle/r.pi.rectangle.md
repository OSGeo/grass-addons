## DESCRIPTION

*r.pi.rectangle* converts sampling points (e.g. GPS coordinates) of the
corner of a sampling site into an area by generating a defined
rectangle. Generates a rectangle based on a corner coordinate.

This modules aims at generating sampling areas which are only known by
the coordinate of one corner. The input are single points, while the
output are areas representing the corresponding area for each of the
single points/coordinates.

## NOTES

The areas can only be generated horizontally, not diagonal. This can be
added as wish and might be implemented in the future.

## EXAMPLE

An example for the North Carolina sample dataset:

```sh
g.region -d
...
```

## SEE ALSO

*[r.pi.corearea](r.pi.corearea.md), [r.pi.corr.mw](r.pi.corr.mw.md),
[r.pi.csr.mw](r.pi.csr.mw.md), [r.pi.export](r.pi.export.md),
[r.pi.graph](r.pi.graph.md), [r.pi.graph.dec](r.pi.graph.dec.md),
[r.pi.graph.pr](r.pi.graph.pr.md), [r.pi.graph.red](r.pi.graph.red.md),
[r.pi.grow](r.pi.grow.md), [r.pi.import](r.pi.import.md),
[r.pi.index](r.pi.index.md), [r.pi.lm](r.pi.lm.md),
[r.pi.odc](r.pi.odc.md), [r.pi.prob.mw](r.pi.prob.mw.md),
[r.pi](r.pi.md)*

## AUTHORS

Programming: Elshad Shirinov  
Scientific concept: Dr. Martin Wegmann  
Department of Remote Sensing  
Remote Sensing and Biodiversity Unit  
University of Wuerzburg, Germany

Port to GRASS GIS 7: Markus Metz
