## DESCRIPTION

*r.in.vect* transforms an external vector file (like GeoPackage) into a
raster file and imports it into GRASS GIS. Optionally, attributes from
the vector layer can be converted to raster category labels.

When users have a vector file that they want to convert to a raster map,
they would normally import the vector map into GRASS GIS using, e.g.,
*v.in.ogr*, and subsequently convert the resulting vector into a raster
map using *v.to.rast*. Because of the topological vector format of GRASS
GIS, importing large complex vector maps can be slow. To speed up the
process, *r.in.vect* converts the user-defined vector file to an
intermediate geoTIF file (using
[gdal.rasterize](https://gdal.org/api/python/utilities.html#osgeo.gdal.Rasterize))
and imports it into GRASS GIS.

The objects in the vector map will be assigned an user-defined value
using the **value** parameter. Alternatively, the user can use the
**attribute\_column** to specify the name of an existing column from the
vector map's attribute table. The values in that column will be used as
raster values in the output raster map.

## Notes

By default, *r.in.vect* will only affect data in areas lying inside the
boundaries of the current computational region. Before running the
function, users should therefore ensure that the computational region is
correctly set, and that the region's resolution is at the desired level.
Alternatively, users can use the **-v** flag to set the exent of the
raster layer to that of the vector layer. To ensure that the resulting
raster map cleanly aligns with the computational region, the extent may
be slightly larger than that of the vector layer.

If the coordinate reference system (CRS) of the vector file differs from
that of the mapset in which users want to import the raster, the vector
file will be first reprojected using *ogr2ogr*.

The **label\_column** parameter can be used to assign raster category
labels. Users should check if each unique value from the category column
has one corresponding label in the label column. If there are categories
with more than one label, the first from the label column will be used
(and a warning will be printed).

With the **-d** flag, all pixels touched by lines or polygons will be
updated, not just those on the line render path, or which center point
is within the polygon. For lines, this is similar to setting the **-d**
flag in *v.to.rast*.

Note that this will make a difference for complex and large vector
layers. For simple and small vector layers, it is probably faster to
import the vector layer first and converting it to a raster in GRASS.

## EXAMPLE

The examples of *r.in.vect* use vector maps from the [North Carolina
sample data set](https://grass.osgeo.org/download/data/).

### Example 1

First, export a vector layer as a GeoPackage.

```sh
# Export the geology vector map as Geopackage
v.out.ogr input=geology@PERMANENT output=geology.gpkg format=GPKG
```

Import the geology.gpkg as raster. Raster cells overlapping with the
vector features will be assigned a value of 1, and the other raster
cells null. If you have RAM to spare, increase the memory to speed up
the import.

```sh
# Set the region
g.region -a vector=geology res=500

# Import the GeoPackage
r.in.vect input=geology.gpkg \
output=geology_rast \
value=1 \
memory=2000
```

[![image-alt](r_in_vect_im01.png)](r_in_vect_im01.png)  
*Figure 1: The geology vector file was converted to, and imported as a
raster into GRASS GIS, using the default settings.*

If the GeoPackage file (or any other data source) has multiple layers,
users need to specify which layer to use with the **layer** parameter.
Otherwise, the first layer will be selected.

### Example 2

Import the geology.gpkg as raster. Specify the column holding the values
to use as raster values and the column holding the labels for the raster
values.

```sh
# Import the layer
r.in.vect input=geology.gpkg \
output=geology_rast2 \
attribute_column=GEOL250_ \
rat_column=GEO_NAME
memory=2000

# Assign random colors
r.colors map=geology_rast2 color=random
```

[![image-alt](r_in_vect_im02.png)](r_in_vect_im02.png)  
*Figure 2: The geology vector file converted to raster and imported into
GRASS GIS using the values from the vector attribute column GEOL250\_ as
raster values.*

### Example 3

First, set the resolution to 1 meter. Next, export the busroute6 vector
map as GeoPackage, and import it as a raster. Use the **-v** flag to
ensure the extent of the raster matches that of the vector (by default,
the bounding box of the raster map will match that of the current
computational region).

```sh
# Set the resolution to 1 m
g.region -a res=1

# Export the busrout6 vector layer
v.out.ogr input=busroute6@PERMANENT \
type=line \
output=busroute6.gpkg \
format=GPKG

# Import it as raster layer, using the extent of the vector layer
r.in.vect -v input=busroute6.gpkg \
output=busroute6_1 \
value=1 \
memory=2000
```

[![image-alt](r_in_vect_im03.png)](r_in_vect_im03.png)  
*Figure 3: The busroute6 vector file converted to raster and imported
into GRASS GIS using the extent of the vector map.*

### Example 4

The same as above, but using the **-d** flag to create densified lines.

```sh
# Import vector as a raster map, using the extent of the vector
r.in.vect -v -d \
input=busroute6.gpkg \
output=busroute6_2 \
value=1 \
memory=2000
```

[![image-alt](r_in_vect_im04.png)](r_in_vect_im04.png)  
*Figure 4: Rasterize the busroute 6 vector map using the **-d** flag to
create densified lines by adding extra cells (shown in red). This avoids
gaps or lines that consist of cells that are only diagonally connected.*

## SEE ALSO

*[v.to.rast](https://grass.osgeo.org/grass-stable/manuals/v.to.rast.html),*

## AUTHORS

Paulo van Breugel ([ecodiv.earth](https://ecodiv.earth))  
Applied Geo-information Sciences  
[HAS green academy, University of Applied
Sciences](https://www.has.nl/)
