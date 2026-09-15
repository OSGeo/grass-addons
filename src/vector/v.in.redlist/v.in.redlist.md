## DESCRIPTION

*v.in.redlist* imports [IUCN](https://www.iucn.org) [Red
List](https://www.iucnredlist.org/) [Spatial
Data](https://www.iucnredlist.org/resources/list/spatial-data). This
data is by definition in WGS84 geographic coordinates.

By the *-l* flag species in column 'binomial' of the attribute table are
listed. The species in column 'binomial' can be exported to a text file
by the *-s* flag.

One of the species mentioned by *-l* or *-s* flag has to be specified
for importing.

## EXAMPLE

```sh
  # list species in column 'binomial' of the attribute table by -l flag
  v.in.redlist -l input=GYMNOPHIONA.shp

  # export species in column 'binomial' of the attribute table into a text file by -s flag
  v.in.redlist -s input=GYMNOPHIONA.shp dir=C:\data\iucn\GYMNOPHIONA

  # import spatial data for a user defined species
  v.in.redlist input=GYMNOPHIONA.shp /
  output=Scolecomorphus_vittatus species_name=Scolecomorphus vittatus
 
```

## SEE ALSO

*[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*

## AUTHOR

Helmut Kudrnovsky
