## DESCRIPTION

*r.prominence* calculates the average difference between a central cell
and its neighbors. It approximated the terrain 'ruggedness' by looking
at average differences in elev\_lid792\_1m within a given neighborhood
The *radius* is specified in number of map rows/columns.

## EXAMPLE

North Carolina sample region:

```sh
g.region raster=elev_lid792_1m

# get region rows/columns
g.region -g

# calculate prominence (radius of 50 map rows)
r.prominence input=elev_lid792_1m output=prominence radius=50

# visualize over shaded DEM
r.relief input=elev_lid792_1m output=elev_lid792_1m_shaded

d.mon wx0
d.shade shade=elev_lid792_1m_shaded color=prominence
```

## AUTHOR

Benjamin Ducke (benjamin.ducke - oxfordarch.co.uk)  
Update to GRASS GIS 7: Markus Neteler -
[mundialis](https://www.mundialis.de/)
