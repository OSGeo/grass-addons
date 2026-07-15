## DESCRIPTION

*v.convert.all* converts all GRASS 5.0/5.3/5.4 vectors in the current
mapset into GRASS 7 vectors.

## NOTES

Vector maps from 5.0/5.3/5.4 and 7 do not interfere. They are stored in
different directories, so the same names can be kept. Old vector maps
can be listed with *g.list oldvect*.

To convert back from 7 to 6 vector format, use *v.build* in GRASS 6.

To convert back from 6.0 into the 5.0/5.3/5.4 vector format, use
*v.out.ogr* (to SHAPE format) and then *v.in.shape* in the old GRASS
program.

As this GRASS version uses SQL for attribute management, there are some
[SQL restrictings concerning the file names](sql.md). This script
changes dots (e.g. "foo.bar") in old vector map names into underline(s)
(e.g. "foo\_bar").

## EXAMPLE

To convert all old vector maps in the current mapset to the new vector
format:

```sh
v.convert.all
```

## SEE ALSO

*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[v.convert](https://grass.osgeo.org/grass-stable/manuals/v.convert.html),
[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html),
[v.out.ogr](https://grass.osgeo.org/grass-stable/manuals/v.out.ogr.html)*

## AUTHOR

Markus Neteler, ITC-Irst, Trento, Italy
