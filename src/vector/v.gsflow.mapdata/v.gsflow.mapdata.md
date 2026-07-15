## DESCRIPTION

*v.gsflow.mapdata* allows the user to add attributes from any raster or
vector (area or point) data set to a GSFLOW set of HRUs, MODFLOW grid
cells, gravity reservoirs, stream segments, or stream reaches. It does
so by using either an averaging or a nearest-neighbor approach,
depending on the type of both the data source geometry (raster, vector
area, vector point) and, if it is a vector, the data source in the
column (integer, string (varchar), or float (double precision)).  
Nearest-neighbor
([v.distance](https://grass.osgeo.org/grass-stable/manuals/v.distance.html),)
is used for:  
Vector point data  
Vector area data in which the data type in the column that is queried is
integer or varchar  
An average
([v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html),)
is used for:  
Raster data  
Vector area data with data in the column that is queried that is of
"double precision" type  

## SEE ALSO

*[v.gsflow.export](v.gsflow.export),
[v.gsflow.gravres](v.gsflow.gravres), [v.gsflow.grid](v.gsflow.grid),
[v.gsflow.hruparams](v.gsflow.hruparams.md),
[v.gsflow.reaches](v.gsflow.reaches.md),
[v.gsflow.segments](v.gsflow.segments.md),
[r.gsflow.hydrodem](r.gsflow.hydrodem.md),
[v.stream.inbasin](v.stream.inbasin.md),
[v.stream.network](v.stream.network.md)*

## AUTHOR

Andrew D. Wickert
