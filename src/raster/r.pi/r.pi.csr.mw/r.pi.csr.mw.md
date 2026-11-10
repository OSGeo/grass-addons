## DESCRIPTION

Complete Spatial Randomness (CSR) analysis based on a moving window.
This function uses either the Clark and Evans (1954) or Donnelly (1978)
aggregation index for testing of clustering of point patterns.

## NOTES

...

## EXAMPLE

An example for the North Carolina sample dataset: Compute the CSR for
the whole landscape of *landclass96* using class 5 (1000 iteration)
using the Clark Evans method:  

```sh
v.random output=randompoints n=100 zmin=0.0 zmax=0.0
v.to.rast input=randompoints output=randompoints  use=val val=1
r.pi.csr.mw input=randompoints keyval=1 n=1000 method=clark_evans output=csr1
```

The results for the whole landscape is prompted to the console. Compute
the CSR for a defined moving window size of *landclass96* using class 5
(1000 iteration, Clark Evans method):  

```sh
r.pi.csr.mw input=randompoints keyval=5 n=1000 method=clark_evans size=7 output=csr1
```

## SEE ALSO

*[r.pi.corearea](r.pi.corearea.md), [r.pi.corr.mw](r.pi.corr.mw.md),
[r.pi.export](r.pi.export.md), [r.pi.graph](r.pi.graph.md),
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
