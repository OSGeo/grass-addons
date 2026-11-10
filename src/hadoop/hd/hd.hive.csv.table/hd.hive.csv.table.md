## DESCRIPTION

*hd.hive.csv.table* helps to create Hive table for storing data in CSV
format

## NOTES

Spatial Framework from ESRI supports reading from several file format.
The Framework allows creating geometric data type from WKB, JSON and
GeoJSON. Table can be created from hiveserver2 command line or with
using module *hd.hive.csv.table*. Defining feature of table is provided
using parameters and flags of module. It helps to user make CSV based
table without advanced knowledge of Hive syntax.

## EXAMPLES

Creating table for storing coordinates.

```sh
hd.hive.json.table driver=hiveserver2 table=csv driver=hiveserver2 table=json struct="type string, properties STRUCT<cat:SMALLINT>, geometry string" -e -d
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
