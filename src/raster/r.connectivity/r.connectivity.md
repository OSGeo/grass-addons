## DESCRIPTION

*r.connectivity* is a toolset for conducting connectivity analysis of
ecological networks. The toolset consists of three modules:

  - [r.connectivity.distance](r.connectivity.distance.md)
  - [r.connectivity.network](r.connectivity.network.md)
  - [r.connectivity.corridors](r.connectivity.corridors.md)

All the modules of the r.connectivity toolset can be installed in GRASS
as follows:

```sh
g.extension operation=add extension=r.connectivity
```

## NOTES

The tools require the following underlying libraries and software:  

  - Cran R
  - igraph and the igraph package for R
  - ghostscript

## EXAMPLE

An example for a full workflow is provided in the manual of the
individual tools applied in the following order:
[r.connectivity.distance](r.connectivity.distance.md),
[r.connectivity.network](r.connectivity.network.md)
[r.connectivity.corridors](r.connectivity.corridors.md)

## REFERENCE

**Framstad, E., Blumentrath, S., Erikstad, L. & Bakkestuen, V. 2012**
(in Norwegian): Naturfaglig evaluering av norske verneområder.
Verneområdenes funksjon som økologisk nettverk og toleranse for
klimaendringer. NINA Rapport 888: 126 pp. Norsk institutt for
naturforskning (NINA), Trondheim.
<https://www.nina.no/archive/nina/PppBasePdf/rapport/2012/888.pdf>

## SEE ALSO

*[r.connectivity.distance](r.connectivity.distance.md),
[r.connectivity.network](r.connectivity.network.md)
[r.connectivity.corridors](r.connectivity.corridors.md)
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html)
[v.distance](https://grass.osgeo.org/grass-stable/manuals/v.distance.html)*

## AUTHOR

For authors, please refer to each module of r.connectivity.
