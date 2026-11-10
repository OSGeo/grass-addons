## DESCRIPTION

*hd.hdfs.in.vector* module is provide conversion of GRASS map serialized
GeoJSON and copy it to HDFS

## NOTES

Vector maps in native GRASS format are not suitable for serialization
which is needed to exploit the potential of spatial frameworks for
Hadoop. The effective way and in the most cases the only possible is to
store spatial data in JSON, especially GeoJSON. This format suits well
for serialization and library for reading is available in catalog of
Hive. Module [hd.hdfs.in.vector](hd.hdfs.in.vector.md) supports
transformation of GRASS map to GeoJSON format and transfer to HDFS.
Behind the module there are two main steps. Firstly, the map is
converted to GeoJSON using *v.out.ogr* and edited to format which is
suitable for parsing by widely used SerDe functions for Hive. After
that, custom GeoJSON format is uploaded to the destination on HDFS. By
default, the HDFS path is set to
*hdfs://grass\_data\_hdfs/LOCATION\_NAME/MAPSET/vector*. In addition,
hd.hdfs.\* package also includes module
[hd.hdfs.in.fs](hd.hdfs.in.fs.md) which allows transfer of external
files to HDFS. Usage of this module becomes important for uploading CSV
or GeoJSON files outside of GRASS. For uploading external GoeJSON files
to HDFS it is necessary to modify its standardized format. The
serialization for JSON has several formatting requirements. See
documentation on wiki page.

## EXAMPLES

PUT vector map to HDFS

```sh
hd.hdfs.in.vector  driver=webhdfs  hdfs=/data map=klad_zm10 layer=1
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
