## DESCRIPTION

The t.rast.out.xyz module exports a space time raster dataset as a list
of x,y,z values into an ASCII text file.

## NOTES

By default, this module does not export x,y coordinates for raster cells
containing a NULL value. This includes cells masked by a raster MASK.
However, using the flag **-i** also these raster cells will be included
in the exported data. *t.rast.out.xyz* is simply a front-end for
"`r.out.xyz`".

## EXAMPLE

```sh
# export strds without NULL cells
t.rast.out.xyz strds=mystrds output=/tmp/mystrds.csv

# export strds including NULL cells and for a certain time period
t.rast.out.xyz -i strds=mystrds output=/tmp/mystrds.csv \
 where="start_time > '2010-01-01 00:00:00'"
```

## SEE ALSO

[r.out.xyz](https://grass.osgeo.org/grass-stable/manuals/r.out.xyz.html),
[t.rast.out.vtk](t.rast.out.vtk.md)

## AUTHOR

Luca Delucchi, *Fondazione Edmund Mach*
