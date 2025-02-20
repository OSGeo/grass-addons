## DESCRIPTION

*v.in.osm* imports OpenStreetMap data.

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

## REQUIREMENTS

PostgreSQL, PostGIS,
[osm2pgsql](https://wiki.openstreetmap.org/wiki/Osm2pgsql)

## SEE ALSO

*[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*

## AUTHOR

Stepan Turek
