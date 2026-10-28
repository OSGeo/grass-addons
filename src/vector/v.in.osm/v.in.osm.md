## DESCRIPTION

*v.in.osm* imports OpenStreetMap data.

The feature types follow the geometry of the selected **table** (OGR
layer): polygon layers (e.g. `multipolygons` of an OSM/PBF file or
`planet_osm_polygon` of an osm2pgsql database) are imported as areas
(boundaries and centroids, with their attributes), point and line layers as
points and lines. Types given in **type** that do not match the layer
geometry are ignored.

By default the selected features (after the **where** filter) are
reprojected to the coordinate reference system of the current project. With
the **-o** flag the data are imported without reprojection, assuming they
are already in the project's CRS.

## NOTES

Line layers are split at every vertex and rebuilt into polylines
(*v.split*, *v.build.polylines*); polygon layers are imported directly with
*v.in.ogr* so that multipolygon rings form areas.

Reprojection is done with GDAL (a temporary GeoPackage in the project CRS)
before the import.

## EXAMPLES

Import from PostgreSQL DB:

```sh
v.in.osm input="PG:host=localhost dbname=gis user=ostepok" table=planet_osm_line \
         type=point,line output=roads where="highway is not null"
```

Import from OSM PBF file:

```sh
v.in.osm input=saarland-latest.osm.pbf table=lines type=point,line output=roads \
         where="highway is not null"
```

Import OSM buildings and land use as areas into a projected project:

```sh
v.in.osm input=saarland-latest.osm.pbf table=multipolygons output=buildings \
         where="building IS NOT NULL"
v.in.osm input=saarland-latest.osm.pbf table=multipolygons output=landuse \
         where="landuse IS NOT NULL OR \"natural\" IS NOT NULL"
```

## REQUIREMENTS

GDAL Python bindings (OSM driver). For database input: PostgreSQL, PostGIS,
[osm2pgsql](https://wiki.openstreetmap.org/wiki/Osm2pgsql)

## SEE ALSO

*[v.build.polylines](https://grass.osgeo.org/grass-stable/manuals/v.build.polylines.html),
[v.import](https://grass.osgeo.org/grass-stable/manuals/v.import.html),
[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*

## AUTHORS

Stepan Turek
