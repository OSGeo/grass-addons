## DESCRIPTION

*v.build.pg* builds PostGIS topology for feature tables linked via
*[v.external](https://grass.osgeo.org/grass-stable/manuals/v.external.html)*.

## NOTES

Note that [PostGIS
Topology](https://trac.osgeo.org/postgis/wiki/UsersWikiPostgisTopology)
extension is currently under development. *v.build.pg* requires
**PostGIS 2.0.0+**.

Existing PostGIS topology schema can be overwrite by **--overwrite**
flag.

*v.build.pg* calls PostGIS functions:

1. [CreateTopology()](https://www.postgis.net/docs/manual-dev/CreateTopology.html)
    to create topology schema in the database,
2. [AddTopoGeometryColumn()](https://www.postgis.net/docs/manual-dev/AddTopoGeometryColumn.html)
    to add a topogeometry column to an existing feature table, and
3. [toTopoGeom()](https://www.postgis.net/docs/manual-dev/toTopoGeom.html)
    to create a new topo geometry from the simple feature geometry.

## EXAMPLES

### Workflow example

Export vector map into PostGIS:

```sh
v.out.ogr input=bridges output=PG:dbname=pgis_nc format=PostgreSQL
```

Create a new vector map as a link to PostGIS table:

```sh
v.external input=PG:dbname=pgis_nc layer=bridges
```

Check metadata:

```sh
v.info map=bridges

...
 |----------------------------------------------------------------------------|
 | Map format:      PostGIS (PostgreSQL)                                      |
 | DB table:        public.bridges                                            |
 | DB name:         pgis_nc                                                   |
 | Geometry column: wkb_geometry                                              |
 | Feature type:    point                                                     |
 |----------------------------------------------------------------------------|
...
```

Build PostGIS topology for the link:

```sh
v.build.pg map=bridges

...
Topology topo_bridges (6), SRID 900914, precision 1
10938 nodes, 0 edges, 0 faces, 10938 topogeoms in 1 layers
Layer 1, type Puntal (1), 10938 topogeoms
 Deploy: public.bridges.topo
...
```

### Dry run

For testing issues use **-p** flag.

```sh
v.build.pg map=bridges

Creating new topology schema...

SELECT topology.createtopology('topo_bridges', \
find_srid('public', 'bridges', 'wkb_geometry'), 1)

Adding new topology column...

SELECT topology.AddTopoGeometryColumn('topo_bridges', \
'public', 'bridges', 'topo', 'point')

Building PostGIS topology...

UPDATE bridges SET topo = topology.toTopoGeom(wkb_geometry, \
'topo_bridges', 1, 1)


SELECT topology.TopologySummary('topo_bridges')
```

## SEE ALSO

*[v.external](https://grass.osgeo.org/grass-stable/manuals/v.external.html),
[v.out.ogr](https://grass.osgeo.org/grass-stable/manuals/v.out.ogr.html),
[v.out.postgis](https://grass.osgeo.org/grass-stable/manuals/v.out.postgis.html),
[v.build](https://grass.osgeo.org/grass-stable/manuals/v.build.html)*

## AUTHOR

Martin Landa, Czech Technical University in Prague, Czech Republic
