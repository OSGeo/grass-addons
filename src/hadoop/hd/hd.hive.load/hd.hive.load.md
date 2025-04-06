## DESCRIPTION

*hd.hive.load* module allows to insert(load) data stored in HDFS into
Hive table

## NOTES

Module *hd.hive.load* provides option to load data to the table.
Availability of this module ensures more space within building of the
workflow especially using python scripting or [graphical modeler of
GRASS](https://grass.osgeo.org/grass-stable/manuals/wxGUI.gmodeler.html),
.

## EXAMPLES

Below is example of HQL command: *LOAD DATA INPATH
'/data/europe\_latest\_fix.csv' OVERWRITE INTO TABLE europe;*

```sh
hd.hive.load driver=hiveserver2 table=europe path=/data/europe_latest_fix.csv
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
