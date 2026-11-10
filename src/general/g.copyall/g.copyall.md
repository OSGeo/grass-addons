## DESCRIPTION

***g.copyall*** copies maps/files of a specified from a selected mapset
to the current working mapset. All maps/files can be copied or a subset
of maps/files specified by a wildcard pattern or regular expression.
Optionally, a prefix can be added to all files copied and vector
topology can be rebuilt to match currently running version of GRASS.

## EXAMPLES

Copy all raster maps from mapset "test" to current mapset and prefix
them with "fromtest":

```sh
g.copyall mapset=test output_prefix=fromtest
```

Copy all vector maps beginning with "s" from mapset "test" to current
mapset:

```sh
g.copyall mapset=test datatype=vect filter="s*"
```

## SEE ALSO

*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[g.copy](https://grass.osgeo.org/grass-stable/manuals/g.copy.html)*

## AUTHOR

Michael Barton (Arizona State University, USA)
