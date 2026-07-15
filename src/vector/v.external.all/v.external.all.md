## DESCRIPTION

*v.external.all* creates (using
*[v.external](https://grass.osgeo.org/grass-stable/manuals/v.external.html)*)
in the current mapset new pseudo-vector maps for all OGR layers from
given OGR datasource (**input** option).

## EXAMPLES

### PostGIS

List available feature tables in given PostGIS database

```sh
v.external.all -l input=PG:dbname=pgis_nc

PostGIS database contains 55 feature table(s):
boundary_county
boundary_municp
bridges
busroute1
busroute11
busroute6
busroute_a
busroutesall
busstopsall
censusblk_swwake
census_wake2000
...
```

Create links (ie. pseudo-vector maps) in the current mapset for all
PostGIS feature tables

```sh
v.external.all input=PG:dbname=pgis_nc
```

### Esri Shapefile

```sh
v.external.all -l input=~/geodata/ncshape/
Data source (format 'ESRI Shapefile')
contains 44 layers:
poi_names_wake
schools_wake
urbanarea
geodetic_swwake_pts
usgsgages
busroute_a
busroute6
hospitals
...
```

```sh
v.external.all -l input=~/geodata/ncshape/
```

## AUTHOR

Martin Landa, Czech Technical University in Prague
