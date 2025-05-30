## DESCRIPTION

*v.to.rast.multi* creates a raster map for each selected numeric column
of the attribute table of a vector map. The purpose is to provide a
simple and efficient way to rasterize different attributes of vector
maps with multiple numeric value columns.

It is a simple wrapper around *v.to.rast* and most of the options from
that module are available. *v.to.rast.multi* works as follows: First,
(only) the key column is rasterized with *v.to.rast*. Then
reclassification rules are generated for all selected attribute columns
and the **key\_column** and reclass maps are created with *r.reclass*.

Because *r.relass* only handles integer data and rounds data with
floating point precision, the number of significant digits to preserve
during reclassification can be defined with the **ndigits** option. Also
text labels can be provided in the **label\_columns** option.

If the **label\_columns** or **ndigits** are given, the number and order
of provided values has to correspond to the number and order of the
selected **attribute\_columns**.

## EXAMPLE

This example is based on the North Carolina sample location
(nc\_spm\_08\_grass7) which can be downloaded from the [GRASS GIS
website](https://grass.osgeo.org/download/data/).

```sh
# Create raster maps for RINGS_OK amd TRACT attribute of the census_wake2000 map
# Note: RINGS_OK is of type integer, so 0 digits need to be preserved
v.to.rast.multi --o --v input=census_wake2000 type=area \
output=vrastmulti attribute_columns="RINGS_OK,TRACT" \
label_columns="ID,TRACTID" memory=3000 ndigits="0,4" separator=","
```

## SEE ALSO

*[v.to.rast](https://grass.osgeo.org/grass-stable/manuals/v.to.rast.html),
[r.reclass](https://grass.osgeo.org/grass-stable/manuals/v.what.strds.html)*

## AUTHOR

Stefan Blumentrath, Norwegian Institute for Nature Research (NINA)
