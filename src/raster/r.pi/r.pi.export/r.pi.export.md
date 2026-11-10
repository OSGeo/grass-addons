## DESCRIPTION

This module exports raster patch values (no single pixels, but single
individual patch values), which can be used for subsequent analysis in R
and later import into GRASS again, using [r.pi.import](r.pi.import.md).

## NOTES

This module...

## EXAMPLE

An example for the North Carolina sample dataset: generating a patch
index map for later export:

```sh
r.pi.index input=landclass96 output=landclass96_forestclass5_area keyval=5 method=area
```

export this resulting map:

```sh
r.pi.export input=landclass96_forestclass5_area output=patch_area_out values=patch_area_values id_raster=forestclass5_ID stats=average,variance,min
```

various resulting files are generated:  
*patch\_area\_out*: a text file with the *average*, *variance* and
*minimum* statistics as defined above and additionally informaton about
the percentage coverage (*landcover*) and the number of fragments
(*number*) of the analysed landcover.  
*patch\_area\_values*: a text file with the actual patch values not the
statistics. The first column is providing the corresponding patch ID,
which is also existing in the *forestclass5\_ID* raster map
(here:0-878). The second column is providing the percentage cover of
each patch (sum is equal the overall coverage: 0.506). The third column
is holding the actual patch index value (here area; e.g. patch 0: 12).

## SEE ALSO

*[r.pi.corearea](r.pi.corearea.md), [r.pi.corr.mw](r.pi.corr.mw.md),
[r.pi.csr.mw](r.pi.csr.mw.md), [r.pi.graph](r.pi.graph.md),
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
