## DESCRIPTION

*v.in.gbif* imports [GBIF](https://www.gbif.org/) species distribution
data. GBIF data is by definition in WGS84 geographic coordinates.

The species distribution data downloaded from
[GBIF](https://www.gbif.org/) hast to be unzipped before importing the
csv file.

*v.in.gbif* saves the data to an intermediate [GDAL](https://gdal.org)
[VRT - Virtual Datasource](https://gdal.org/drivers/vector/vrt.html)
which will be imported by
[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html).
The VRT data set can be copied to a user defined directory by *-c* flag
and used in any GDAL aware software. As some column names in the
original data set are similar to [SQL reserverd key
words](https://www.postgresql.org/docs/devel/sql-keywords-appendix.html),
the columns will renamed with the prefix *g\_*.

By the *-r* flag an on-the-fly reprojection of the data can be invoked
using
[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html),
if the location is not in WGS84. Quality of on-the-fly reprojection is
not garanteed. The traditional reprojection procedure in GRASS GIS can
also be used instead.

## EXAMPLE

```sh
  # import GBIF data
  v.in.gbif input=0004248-150811131857512.csv output=chondrilla

  # create GDAL VRT files based upon GBIF data in user defined directory by -c flag
  v.in.gbif -c input=0004248-150811131857512.csv /
  output=chondrilla dir=C:\data\
 
```

## SEE ALSO

*[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html),
[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html),
[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html),
[v.proj](https://grass.osgeo.org/grass-stable/manuals/v.proj.html)*

## AUTHOR

Helmut Kudrnovsky
