## DESCRIPTION

*g.proj.identify* allows to automaticaly identify the EPSG code from a
given Well-Know Text (WKT) projection string stored in a file. The user
can also print the EPSG code of the current location. The conversion
from a given EPSG code to WKT and proj4 is supported.

## EXAMPLE

```sh
# print EPSG code of current Location - use without parameters
g.proj.identify

# identify EPSG code from WKT definition stored in file 'myproj.wkt'
g.proj.identify wkt=myproj.wkt

# print WKT and proj4 for given EPSG code, independent from current location
g.proj.identify -p -w epsg=4326
```

## SEE ALSO

*[g.proj](https://grass.osgeo.org/grass-stable/manuals/g.proj.html),
[m.proj](https://grass.osgeo.org/grass-stable/manuals/m.proj.html),
[r.proj](https://grass.osgeo.org/grass-stable/manuals/r.proj.html),
[v.proj](https://grass.osgeo.org/grass-stable/manuals/v.proj.html)*

## AUTHORS

Matej Krejci, [OSGeoREL](https://geo.fsv.cvut.cz/gwiki/osgeorel) at the
Czech Technical University in Prague, developed during [Google Summer of
Code 2015](https://trac.osgeo.org/grass/wiki/GSoC/2014/MetadataForGRASS)
(mentor: Martin Landa)
