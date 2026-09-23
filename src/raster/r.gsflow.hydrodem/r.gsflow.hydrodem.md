## DESCRIPTION

*r.gsflow.hydrodem* generates a hydrologically-correct MODFLOW DEM for
GSFLOW based on higher-resolution flow routing. It does so by taking
minimum grid cell elevations where streams are present, and mean grid
cell elevations elsewhere, while coarsening the resolution to that of
the specified MODFLOW grid resolution.

## REFERENCES

Ng, G.-H. C., A. D. Wickert, R. L. McLaughlin, J. La Frenierre, S.
Liess, and L. Sabeeri (2016), Modeling the role of groundwater and
vegetation in the hydrological response of tropical glaciated watersheds
to climate change, in AGU Fall Meeting Abstracts, H13L–1590, San
Francisco, CA.

## SEE ALSO

[v.gsflow.export](v.gsflow.export),
[v.gsflow.gravres](v.gsflow.gravres), [v.gsflow.grid](v.gsflow.grid),
[v.gsflow.hruparams](v.gsflow.hruparams),
[v.gsflow.reaches](v.gsflow.reaches),
[v.gsflow.segments](v.gsflow.segments),
[v.gsflow.mapdata](v.gsflow.mapdata),
[v.stream.inbasin](v.stream.inbasin),
[v.stream.network](v.stream.network)

## AUTHOR

Andrew D. Wickert
