## DESCRIPTION

*g.rename.many* renames multiple maps at once using
*[g.rename](https://grass.osgeo.org/grass-stable/manuals/g.rename.html)*
module. Old and new names are read from a text file. The file format is
a simple CSV (comma separated values) format with no text delimiter
(e.g. no quotes around cell content). Comma is a default cell delimiter
but it can be changed to anything.

Possible use cases include:

- renaming maps named in a certain language to English when data were
    obtained at national level but the futher collaboration is
    international
- renaming provided sample maps with English names to a national
    language for educational purposes in case English is not appropriate
- preparation of a [GRASS GIS Standardized Sample
    Dataset](https://grasswiki.osgeo.org/wiki/GRASS_GIS_Standardized_Sample_Datasets)
    which requires a certain set of standardized names

## EXAMPLE

### Renaming rasters

First prepare a file with names of raster maps to be renamed. The file
can be prepared in spreadsheet application (and saved as CSV with cell
delimiter comma and no text delimiter) or as a text file in any (plain)
text editor. In any case, the result should be a plain text file with
format and content similar to the following sample:

```sh
landuse96_28m,landuse
geology_30m,geology
soilsID,soils
```

Once the file is prepared, the module can be called:

```sh
g.rename.many raster=raster_names.csv
```

This example worked only with raster maps. However multiple files, one
for each map type, can be used at once.

### Creating a file with current names

A template for renaming can be prepared using
*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html)*
module, for example in command line (bash syntax):

```sh
g.list type=raster mapset=. sep=",
" > raster_names.csv
```

Note that we are using only maps in a current Mapset because these are
the only ones we can rename.

With some further processing file template can be made more complete by
including map names twice (bash syntax):

```sh
g.list type=raster mapset=. | sed -e "s/\(.*\)/\1,\1/g" > raster_names.csv
```

The *sed* expression used here takes whatever is on a line on input and
puts it twice on one line on the output separated by comma.

## SEE ALSO

*[g.rename](https://grass.osgeo.org/grass-stable/manuals/g.rename.html),
[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html)*

## AUTHOR

Vaclav Petras, [NCSU OSGeoREL](https://geospatial.ncsu.edu/osgeorel/)
