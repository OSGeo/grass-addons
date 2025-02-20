## DESCRIPTION

*v.convert* converts GRASS 5.0/5.3/5.4 vectors into 5.7/6.x vectors.

## NOTES

Vector maps from 5.0/5.3/5.4 and 5.7/6.x do not interfere. They are
stored in different directories, so you can use the same names. Old
vector maps can be listed with *g.list oldvect*.

If you need to convert back from 5.7/6.x into the 5.0/5.3/5.4 vector
format, use *v.out.ogr* (to SHAPE format) and then *v.in.shape* in the
old GRASS program. Alternatively use "*v.out.ascii -o*" and
*v.in.ascii*.

As this GRASS version uses SQL for attribute management, there are some
[SQL restrictings concerning the file names](sql.md).

Missing centroids can be added with *v.category*.

## EXAMPLE

```sh
v.convert in=vectormap_from_50 out=vectormap_60
```

## SEE ALSO

[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[v.category](https://grass.osgeo.org/grass-stable/manuals/v.category.html),
[v.convert.all](https://grass.osgeo.org/grass-stable/manuals/v.convert.all.html),
[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html),
[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html),
[v.out.ogr](https://grass.osgeo.org/grass-stable/manuals/v.out.ogr.html)

## AUTHOR

Radim Blazek, ITC-Irst, Trento, Italy
