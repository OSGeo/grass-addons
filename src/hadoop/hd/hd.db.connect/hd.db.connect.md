## DESCRIPTION

*hd.db.connect* providing connection manager for GRASS Hadoop Framework

The module provides storing of connection profiles in default GRASS GIS
database backend which is SQLite by default. The usage of the database
manager is derived from current GRASS db.\* modules. Thus, based on set
up primary connection which is use for all involved modules.

## NOTES

### Defining connection

Parameter *driver* and *conn\_id* are mandatory for each connection
profile. Parameter *driver* defines the protocol for communication with
database and *conn\_id* is a free unique string of connection profile.
Other parameters as *host*, *port*, *login*, *passwd*, *schema*,
*authmechanism* depends on a configuration of database server. After a
new connection is added, the module automatically set the new one as
active. In case of controlling several Hadoop clusters it is suitable to
define its connection profiles and switching between by flag *-a* with
parameter *conn\_id* and *driver*.

### Local hosts

For accessing HDFS from GRASS Hadoop Framework the driver must know all
external IP addresses of master and workers of cluster. After the client
accesses HDFS daemon (port 50700) then it receives message with local
host and port of workers instead of IP address. If the client is running
from different machine than master, these IP addresses and local host
names must be defined. In Linux systems the configuration of local hosts
are declared in file */etc/hosts*.

## EXAMPLES

Defining connection of Hive database (hiserver2 driver):

```sh
hd.db.connect driver=hiveserver2 conn_id=hive_spatial  host=cluster-4-m.c.hadoop port=10000 login=matt schema=default
```

Defining connection of Hadoop Namenode(WebHDFS REST API) :

```sh
hd.db.connect.py driver=webhdfs conn_id=hdfs_spatial login=matt host=cluster-4-m.c.hadoop port=50070
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
