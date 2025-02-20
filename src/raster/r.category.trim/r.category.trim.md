## DESCRIPTION

### Trim redundant category labels and colors

In GRASS you can 'cut out' a subset of a larger raster layer by setting
the extent to something smaller than the extent of the original map
using g.region and/or by setting a mask using r.mask, after which you
simply run r.mapcalc "newmap = oldmap".

You may have noticed that when creating the new map, all category labels
and colour table of the original map are copied over to the new map,
even for category values that are not in the new map. If you are working
with categorical maps, this may not be what you want. See
[here](https://pvanb.wordpress.com/2015/09/22/categorical-maps-and-legends/)
for a more detailed discussion.

With this addon you can trim the category and colour tables so it only
contains category labels and colour definitions for the values present
in the new map. You can do this on the input map, or do this on a copy
of the map.

### Recode to consecutive category values

If you prefer the map to have consecutive values (i.e., without gaps),
there is the option to change the category values to a consecutive
series by setting the n-flag. For example, if the map has the following
categories values and labels (after the redundant category labels have
been removed):

```sh
2 label2
5 label5
9 label9
```

Then the new recoded layer will have the category values and labels:

```sh
1 label2
2 label5
3 label9
```

### Export QGIS color map file

The addon let's you export the categories, category labels and colours
as QGIS colour map file. This is just a simple text file with the raster
categories and corresponding colour definitions and category labels.
QGIS can use this to set the colour and labels for a raster layer. See
[this
blogpost](https://pvanb.wordpress.com/2015/09/22/categorical-maps-and-legends/)
for more details how to use the colour map file in QGIS. Alternatively,
you can also export the categories and category labels as a normal comma
separated values (CSV) file, which can be easily viewed in a spreadsheet
program such as Libre/Open Office Calc, Microsoft Excel, or Google Docs
and can be easily shared together with an exported raster file for users
that use other GIS programs.

## NOTE

The file is only useful for categorical maps. Therefore only integer
maps are accepted as input. To export color maps for continuous raster
layers (or as an alternative to this plugin), have a look at the
r.colors.out\_sld plugin. To get QGIS color files, you need a two-step
approach: (1) create a sld file using the r.colors.out\_sld plugin, and
(2) in QGIS, use the SLD4raster plugin to convert this to a qml file.

When you use the option to recode the map, you need to set an output map
as well. It uses the
*[r.recode](https://grass.osgeo.org/grass-stable/manuals/r.recode.html)*
function, with the 'a' flag set, i.e., the region is aligned to the
input raster map.

## Examples

See
[here](https://pvanb.wordpress.com/grass-gis-categorical-raster-layers-in-qgis)
for examples

## See also

*[r.category](https://grass.osgeo.org/grass-stable/manuals/r.category.html),
[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html),
[r.recode](https://grass.osgeo.org/grass-stable/manuals/r.recode.html)
[r.colors.out\_sld](r.colors.out_sld.md)*

## AUTHOR

Paulo van Breugel, paulo at ecodiv.earth
