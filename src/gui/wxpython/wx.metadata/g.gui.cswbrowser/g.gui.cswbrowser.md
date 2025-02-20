## DESCRIPTION

*g.gui.cswbrowser* supports searching and browsing metadata catalogs
based on [Catalogue Service
(CSW)](https://www.ogc.org/publications/standard/cat/) standard .

The module allows to setting up connection to csw by uri and search
metadata using advanced filter.

## NOTES

For dependencies and installation instructions see the dedicated [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

### Setting up connection

After start g.gui.cswbrowser the connection manager is initialized by
default connection file which includes some well known catalogs.
Connection manager allows to add, to delete and to load connection from
xml file.

### Search and browse catalog

Searching and browsing panel allows to setup request with using custom
filter.

## EXAMPLES

### Query filter

The filter can be defined by limitation of area by bounding box which
can be set by GRASS region or manualy.

### Bounding box

  - Bounding box  
    Bounding box defined spatial extent for limitation of area. Button
    "Map extends" allows to set up values from current GRASS region.

  - Keywords  
    This filter allows to use basic or advance keyword filtering. In the
    simple case user can define single keywords or multiple keywords
    with button "+". Logic operator between keywords is AND(&&). Second,
    advanced is based on OGC list of expressions which means that can be
    set filtr with logic relations between keywords or sets of keywords.
    Dialog for settings kewords text string is under "Advanced"
    checkbox. Syntax of constraints is based on python list syntax. Each
    keywords must be in braces \<'\> or \<"\>.

  - - OR condition  
        a || b || c \["a","b","c"\]
      - AND condition  
        a && b && c \[\["a","b","c"\]\]
      - composition  
        (a && b) || c || d || e \[\["a","b"\],\["c"\],\["d"\],\["e"\]\]
        or \[\["a","b"\],"c","d","e"\]

### Browsing of metadata

In case of successful request, user can browse through results and show
request and response in xml format. If services contains uri of WMS, WFS
or WMS, module allows to add them directly with using upper toolbar.

## SEE ALSO

*[r.info](https://grass.osgeo.org/grass-stable/manuals/r.info.html),
[v.info.iso](v.info.iso.md), [g.gui.metadata](g.gui.metadata.md),
[db.csw.harvest](db.csw.harvest), [db.csw.admin](db.csw.admin),
[db.csw.run](db.csw.run)*

See also related [wiki
page](https://grasswiki.osgeo.org/wiki/ISO/INSPIRE_Metadata_Support).

## AUTHORS

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2015](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentor: Martin Landa)
