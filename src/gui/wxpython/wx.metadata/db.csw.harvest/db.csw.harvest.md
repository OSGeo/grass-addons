## DESCRIPTION

Module *db.csw.harvest* allows to harvest metadata between two
catalogues.

## NOTES

For dependencies and installation instructions see [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).
For importing metadata to local server transactions must be allowed. The
parameter "transactions" is stored in the configure file "default.cfq"
(by default in pycsw installation folder).

## EXAMPLES

Harvesting of a remote catalogue to local:

```sh
db.csw.harvest source=https://geodati.gov.it/RNDT/csw destination=http://localhost:8000/
```

## SEE ALSO

*[r.info](https://grass.osgeo.org/grass-stable/manuals/r.info.html),
[v.info.iso](v.info.iso.md), [g.gui.metadata](g.gui.metadata.md),
[g.gui.cswbrowser](g.gui.cswbrowser.md), [db.csw.admin](db.csw.admin),
[db.csw.run](db.csw.run)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHOR

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2015](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentors: Martin Landa)
