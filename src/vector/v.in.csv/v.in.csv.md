## DESCRIPTION

*v.in.csv* imports rows from a CSV (Comma Separated Value) file into a
vector map as points with attributes. The separator for CSV is comma
(`,`) by default, but it can be set to any single character such as
semicolon (`;`), pipe (`|`), or tabulator.

## NOTES

The module requires the "pyproj" Python package to work.

## EXAMPLES

The following imports CSV file called `latest_sites.csv` in the current
directory into the current mapset as point vector map named
`sampling_sites` using the default coordinate transformation from WGS84.
Latitude and longitude are in columns `Site_Lat` and `Site_Long`.

```sh
v.in.csv input=latest_sites.csv output=sampling_sites latitude=Site_Lat longitude=Site_Long
```

## SEE ALSO

  - *[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html)*
    for the underlying module with finer control (but not coordinate
    transformation),
  - *[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*
    for an alternative CSV import using GDAL/OGR.

## AUTHOR

Vaclav Petras, [NCSU Center for Geospatial
Analytics](https://cnr.ncsu.edu/geospatial/)
