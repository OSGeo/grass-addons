## DESCRIPTION

*hd.hive.select* module allows to query table of Hive.

## NOTES

## EXAMPLES

Below is example of HQL query with redirecting output to file

```sh
hd.hive.select driver=hiveserver2 hql='SELECT linkid from mwrecord' out='tmp/linkid.hql'
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
