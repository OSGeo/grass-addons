## DESCRIPTION

*m.csv.clean* reads a CSV (Comma Separated Value) file, cleans it, and
writes a new CSV file. The separator for CSV is comma (`,`) by default,
but it can be set to any single character such as semicolon (`;`), pipe
(`|`), or tabulator.

## NOTES

Originally, the name for this module was supposed to be *m.csv.polish*
and the module was to be accompanied with module named *m.csv.czech* for
checking the state of the CSV.

## EXAMPLES

### In GRASS GIS shell

The following would apply all the default fixes to the the file
`sampling_sites_raw.csv` and output a cleaned file `sampling_sites.csv`:

```sh
m.csv.clean input=sampling_sites_raw.csv output=sampling_sites.csv
```

### In any shell

The module is not using any information from the current location and
mapset, so it is very easy to run it with an adhoc temporary location by
executing a `grass --exec` command:

```sh
grass --tmp-project XY --exec m.csv.clean input=sampling_sites_raw.csv output=sampling_sites.csv
```

## SEE ALSO

  - *[v.in.csv](v.in.csv.md)* for an addon module for importing CSV as
    vector points with coordinate transformation,
  - *[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html)*
    for importing CSV as vector points with different approach,
  - *[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*
    for an alternative CSV import using GDAL/OGR.

## AUTHOR

Vaclav Petras, [NCSU Center for Geospatial
Analytics](https://cnr.ncsu.edu/geospatial)
