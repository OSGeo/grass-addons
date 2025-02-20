## DESCRIPTION

*v.stream.inbasin* uses the output of *v.stream.network* to select only
those streams (and sub-basins) that are upstream of (and inclusive of) a
selected link in the network. It is used as a step to develop GSFLOW
model inputs for a watershed, but need not be exclusively used for that
purpose. *v.stream.inbasin* expects the stream network attributes
created by *v.stream.network* and named using the names
*v.stream.network* uses by default. In other words, *v.stream.inbasin*
will work on the output *v.stream.network* with default attribute names.

## REFERENCES

  - Ng, G.-H. C., A. D. Wickert, R. L. McLaughlin, J. La Frenierre, S.
    Liess, and L. Sabeeri (2016), Modeling the role of groundwater and
    vegetation in the hydrological response of tropical glaciated
    watersheds to climate change, in AGU Fall Meeting Abstracts,
    H13L–1590, San Francisco, CA.
  - Ng, G-H. Crystal, Andrew D. Wickert, Lauren D. Somers, Leila Saberi,
    Collin Cronkite-Ratcliff, Richard G. Niswonger, and Jeffrey M.
    McKenzie. "GSFLOW–GRASS v1. 0.0: GIS-enabled hydrologic modeling of
    coupled groundwater–surface-water systems." *Geoscientific Model
    Development* 11 (2018): 4755-4777.
    [DOI 10.5194/gmd-11-4755-2018](https://doi.org/10.5194/gmd-11-4755-2018)

## SEE ALSO

*[v.gsflow.hruparams](v.gsflow.hruparams.md),
[v.gsflow.segments](v.gsflow.segments.md),
[v.stream.network](v.stream.network.md)*

## AUTHOR

Andrew D. Wickert
