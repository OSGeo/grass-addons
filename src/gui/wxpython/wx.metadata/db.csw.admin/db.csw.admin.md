## DESCRIPTION

Module *db.csw.admin* allows to handle csw server.

## NOTES

For dependencies and installation instructions see [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## USAGE

For using this module must be installed pycsw libraries. Default path to
configure folder is setup to pycsw install folder(LINUX)
/var/www/html/pycsw in another case, path to config file must by set by
user.

### Configure file

In configure file must be setup few parameters for proper work of pycsw
library.

  - server.home  
    Path to folder with installed pycsw
  - database.homez  
    Path to database with data of catalog. By default is set to SQLite
    database. E.g GRASS GIS sqlite database.
  - server.url  
    For using local serever this parameter should by set to
    <http://localhost:8000/>

```sh
db.csw.harvest source=https://geodati.gov.it/RNDT/csw destination=http://localhost:8000/
```

## SEE ALSO

*[r.info](https://grass.osgeo.org/grass-stable/manuals/r.info.html),
[v.info.iso](v.info.iso.md), [g.gui.metadata](g.gui.metadata.md),
[g.gui.cswbrowser](g.gui.cswbrowser.md),
[db.csw.harvest](db.csw.harvest), [db.csw.run](db.csw.run)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHOR

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2015](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentors: Martin Landa)
