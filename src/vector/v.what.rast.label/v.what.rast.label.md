## DESCRIPTION

*v.what.rast.label* retrieves raster values and labels from one or more
given raster maps for each point stored in the input vector map. The
name of the columns with the raster values start with *ID\_*, followed
by the name of the raster layer from which the values are taken. For the
name of the column with the raster labels, the name of the raster from
which the label is taken is used.

Optionally, the user can define raster layers without labels. In that
case only the raster values are uploaded to a column with the name of
that raster.

Another option is to add columns with point coordinates to the attribute
table of the output vector layer.

The user can opt to include the attribute columns of the input vector
layer in the output. In that case, the columns with the raster values
and labels will appear after the columns from the input vector layer.

## NOTES

Points and centroids with shared category number cannot be processed. To
solve this, unique categories may be added with v.category in a separate
layer. See *v.what.rast* for details.

If you only want to upload raster values at positions of vector points
to the attribute table of that vector layer, use *v.what.rast* instead.

## EXAMPLES

Get the POI within the bounds of the land use map.

```sh
g.region raster=landuse
v.in.region output=regionbounds
v.select ainput=points_of_interest binput=regionbounds output=POI_select operator=within
```

Extract raster values and labels from landuse map. Columns from the
input map (POI\_select) are not included.

```sh
v.what.rast.label vector=POI_select raster=landuse raster2=elevation output=POI_landuse1
```

Extract raster values and labels from landuse map. Use the -0 flag to
include the columns from the input map (POI\_select)

```sh
v.what.rast.label -o vector=POI_select raster=landuse raster2=elevation output=POI_landuse2
```

Extract raster values and labels from landuse map and values from
elevation map. Use the -0 flag to include the columns from the input map
(POI\_select)

```sh
v.what.rast.label -o vector=POI_select@user1 raster=landuse raster2=elevation output=POI_landuse3
```

Extract raster values and labels from landuse map and values from
elevation map. Use the -0 flag to include the columns from the input map
(POI\_select). Use the -c flag to include the point coordinates

```sh
v.what.rast.label -o -c vector=POI_select@user1 raster=landuse@PERMANENT raster2=elevation@PERMANENT output=POI_landuse4
```

## SEE ALSO

*[v.what.rast](https://grass.osgeo.org/grass-stable/manuals/v.what.rast.html),
[v.what.rast.multi](v.what.rast.multi.md) (addon)*

## AUTHORS

Paulo van Breugel | [HAS green academy](https://has.nl), University of
Applied Sciences | [Climate-robust Landscapes research
group](https://www.has.nl/en/research/professorships/climate-robust-landscapes-professorship/)
| [Innovative Bio-Monitoring research
group](https://www.has.nl/en/research/professorships/innovative-bio-monitoring-professorship/)
| Contact: [Ecodiv.earth](https://ecodiv.earth)
