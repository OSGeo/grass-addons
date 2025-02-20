## DESCRIPTION

*v.clean.ogr* cleans non-topological polygons in an OGR datasource by
importing, cleaning, and exporting these polgons. This module should not
be used with polygons that are correctly overlapping, e.g. buffers.

*v.clean.ogr* imports vector data from files and database connections
supported by the [OGR](https://gdal.org/) library into a temporary
location. Only one input layer is imported.

Polygons in the input layer are automatically cleaned during impport.
More thorough cleaning can be achieved by using the **snap** and
**min\_area** options.

The cleaned result is exported to the selected **output** datasource
with "\_clean" appended to the input layer name. Any overlaps are
exported with "\_overlaps" appended to the input layer name.

### Supported Vector Formats

*v.clean.ogr* uses the OGR library which supports various vector data
formats including
[GeoPackage](https://gdal.org/drivers/vector/gpkg.html), [ESRI
Shapefile](https://gdal.org/drivers/vector/shapefile.html), [Mapinfo
File](https://gdal.org/drivers/vector/mitab.html), UK .NTF, SDTS, TIGER,
IHO S-57 (ENC), DGN, GML, GPX, AVCBin, REC, Memory, OGDI, and
PostgreSQL, depending on the local OGR installation. For details see the
[OGR web site](https://gdal.org/drivers/vector/index.html). The OGR
(Simple Features Library) is part of the [GDAL](https://gdal.org)
library, hence GDAL needs to be installed to use *v.clean.ogr*.

The list of actually supported formats can be printed by **-f** flag.

## NOTES

### Topology cleaning

When importing polygons, non-topological polygons are converted to
topological areas. If the input polygons contain errors (unexpected
overlapping areas, small gaps between polygons, or warnings about being
unable to calculate centroids), the import might need to be repeated
using a *snap* value as suggested in the output messages.

The *snap* threshold defines the maximal distance from one to another
vertex in map units (for latitude-longitude locations in degree). If
there is no other vertex within *snap* distance, no snapping will be
done. Note that a too large value can severely damage area topology,
beyond repair.

Further cleaning can be achieved by removing small areas using the
**min\_area** option. Note that units are always squaremeters. Values
for **min\_area** should generally be small, a value of 0.5 can already
clean up lots of artefacts.

## EXAMPLE

Cleaning polygons in a Shapefile in the current directory
*research\_area*

```sh
v.clean.ogr input=research_area layer=research_area output=research_area \
            snap=1e-4 min_area=1 -u --overwrite
```

Two new Shapefile layers "research\_area\_clean" and
"research\_area\_overlaps" may be created in the same directory.

## SEE ALSO

*[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html),
[v.clean](https://grass.osgeo.org/grass-stable/manuals/v.clean.html),
[v.out.ogr](https://grass.osgeo.org/grass-stable/manuals/v.out.ogr.html)*

## AUTHOR

Markus Metz
