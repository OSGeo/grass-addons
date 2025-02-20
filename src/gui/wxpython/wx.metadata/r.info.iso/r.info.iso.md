## DESCRIPTION

*r.info.iso* creates metadata of raster maps according to [ISO
19115](https://www.iso.org/standard/26020.html).

The module also allows conversion of metadata from native GRASS GIS
format to ISO-based format.

## NOTES

For dependencies and installation instructions see [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

### Naming of metadata files and storage

Default location for exported metadata files is *metadata* directory in
the map's mapset. If the name for output metadata file is not specified
by **output** option than the name is built from map's type and its
name. For raster maps, the prefix derived from the current nomenclature
is *raster*, for vector maps *vector*. File ends with *.xml* extension.

For example default metadata file name for raster map "elevation" is
*cell\_elevation.xml*.

### Metadata profile

The *basic* profile is substituted from intersection between items
stored in GRASS native metadata format and INSPIRE profile. The
intersect (subset) includes all available GRASS metadata. Metadata which
cannot be assigned to ISO based attributes are stored in metadata
attribute *abstract*. The *inspire* profile fulfills the criteria of
INSPIRE profile. Values which are not able to get from native GRASS
metadata are filled by text string `'$NULL'`. This rule applies to both
profiles.

## EXAMPLES

Export metadata using *basic* profile (default):

```sh
r.info.iso map=elevation
```

Export metadata using *inspire* profile:

```sh
r.info.iso map=elevation profile=inspire
```

## SEE ALSO

*[r.info](https://grass.osgeo.org/grass-stable/manuals/r.info.html),
[v.info.iso](v.info.iso.md), [g.gui.metadata](g.gui.metadata.md)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHORS

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2014](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentors: Margherita Di Leo, Martin Landa)
