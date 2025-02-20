## DESCRIPTION

This module extracts selected categories from an integer raster map into
a new raster, similarly to
*[v.extract](https://grass.osgeo.org/grass-stable/manuals/v.extract.html)*
for vectors. The categories and color table are preserved.

The category values can be specified as:

  - cat1,cat2,...
  - cat1-cat3
  - cat1-
  - \-cat1
  - and their combination: -cat1,cat2,cat3-cat6

The extent of the new raster can be changed with flag **-c** to fit the
extent of the extracted data. When using flag **-s** output raster is a
reclassified input raster (see
*[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html)*
for details).

## NOTES

This implementation supports only integer raster maps (type CELL).

## EXAMPLES

The following examples are using the full North Carolina sample dataset.
We will extract certain zipcodes. First print zipcodes raster info:

```sh
g.region raster=zipcodes -p
r.info zipcodes -rg
```

```sh
...
rows=1350
cols=1500
min=27511
max=27610
...
```

Now we extract 2 categories and automatically adjust the raster extent
to fit the extracted data.

```sh
r.extract input=zipcodes output=selected_zipcodes cats=27605,27601 -c
r.info selected_zipcodes -rg
```

```sh
...
rows=404
cols=377
min=27601
max=27605
...
```

## SEE ALSO

*[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html)*
(used in this implementation)  
*[v.extract](https://grass.osgeo.org/grass-stable/manuals/v.extract.html)*
(for extracting vector data)

## AUTHOR

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
