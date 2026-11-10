## DESCRIPTION

*hd.esri2vector* module for conversion Hive table stored serialised Esri
GeoJSON to GRASS vector map.

## NOTES

### Usage

By default is exported only geometry features of map. Parameter
*attribute* specify attributes which will be linked to the map. Check
[hd.hdfs.out.vector](hd.hdfs.out.vector.md) for GET Hive table from
Hadoop server.

## EXAMPLES

Conversion of Hive table stored on local computer.

```sh
hd.esri2vector out=europe_aggregation attributes='count int,bin_id int' path=/path/to/hive/table
```

## SEE ALSO

*[hd.hdfs.in.fs](hd.hdfs.in.fs.md),
[hd.hdfs.in.vector](hd.hdfs.in.vector.md),
[hd.hdfs.out.vector](hd.hdfs.out.vector.md),
[hd.hdfs.info](hd.hdfs.info.md), [hd.hive.execute](hd.hive.execute.md),
[hd.hive.csv.table](hd.hive.csv.table.md),
[hd.hive.select](hd.hive.select.md), [hd.hive.info](hd.hive.info.md),
[hd.hive.json.table](hd.hive.json.table.md)*

See also related [wiki page](https://grasswiki.osgeo.org/wiki/).

## AUTHOR

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during master thesis
project 2016 (mentor: Martin Landa)
