## DESCRIPTION

*r.null.all* manages NULL (no-data) values in all raster maps in the
current mapset. Selection can be modified using **pattern** and
**exclude** options. The option **matching** specifies the type of
search pattern use. Python users will find the extended regular
expression syntax (marked as *extended*) as most familiar, while Bash
users may want to use *wildcards* (glob patterns).

## EXAMPLES

All the following examples are using the **-d** flag to run in a *dry
run* mode so that no maps are actually modified. Set all values 1 to
NULL in all raster maps in the current mapset:

```sh
r.null.all setnull=1 -d
```

Change all NULL to zero in all raster maps in the current mapset which
begin with letter t and their name contains at least one other character
(using the extended regular expressions):

```sh
r.null.all null=0 pattern="^t.+" matching=extended -d
```

Set all values 0 to NULL in raster maps in the current mapset which do
not end with the digit 1 (using the wildcards syntax):

```sh
r.null.all setnull=0 exclude="*1" matching=wildcards -d
```

Set all values 0 to NULL in raster maps in the current mapset which do
not end with the digit 1 (using extended regular expressions):

```sh
r.null.all setnull=0 exclude=".*1" matching=extended -d
```

## SEE ALSO

*[r.null](https://grass.osgeo.org/grass-stable/manuals/r.null.html),
[g.proj.all](g.proj.all.md), [g.copyall](g.copyall.md),
[g.rename.many](g.rename.many.md)*

## AUTHOR

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
