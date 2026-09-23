## DESCRIPTION

*v.in.wfs2* imports OGC WFS maps (Web Feature Service) from external
servers.

## EXAMPLES

Parks in Canada:

```sh
v.in.wfs2 url=http://www2.dmsolutions.ca/cgi-bin/mswfs_gmap output=parks srs=42304 layers=park wfs_version=1.1.0
```

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.in.wms](https://grass.osgeo.org/grass-stable/manuals/r.in.wms.html),
[v.in.ogr](https://grass.osgeo.org/grass-stable/manuals/v.in.ogr.html)*

## AUTHOR

Stepan Turek
