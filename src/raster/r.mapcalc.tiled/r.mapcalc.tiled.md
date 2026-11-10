## DESCRIPTION

*r.mapcalc.tiled* cuts a raster input map into tiles and runs
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)
over these tiles before patching the result together into a single
output raster map.

The user provides the map calculation **expression**. The output map
name is automatically extracted from that expression by extracting the
string before the '='. If the **expression** is more complex, the user
can also provide the the output map name with the parameter **output**

Tiles can be defined with the **width**, **height** and **overlap**
parameters. If no **width** and **height** is specified, they are
automatically computed from the number of processes and current
computational region (with GRASS GIS v8.2 and above). For example, 8
processes result in 8 tiles where the tile width is equal to the number
of columns. If **nprocs** is higher than one, these tiles will be
processed in parallel.

The **mapset\_prefix** parameter ensures that the temporary mapsets
created during the tiled processing have unique names. This is useful if
the user runs *r.mapcalc.tiled* several times in parallel (e.g. in an
HPC environment).

Option **patch\_backend** can switch how the resulting tiles are merged.
With **patch\_backend=RasterRow** (default) the original
[GridModule](https://grass.osgeo.org/grass-stable/manuals/libpython/pygrass.modules.grid.html)
implementation is used. With **patch\_backend=r.patch** module
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html) is
used with the number of cores specified with **nprocs**. This backend
can only be used with 0 overlap.

## EXAMPLE

Run **r.mapcalc** over tiles with size 1000x1000 using 4 parallel
processes (North Carolina sample dataset):

```sh
g.region raster=ortho_2001_t792_1m
r.mapcalc.tiled expression="bright_pixels = if(ortho_2001_t792_1m > 200, 1, 0)" \
   width=1000 height=1000 nprocs=4
```

## SEE ALSO

[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)

## AUTHOR

Moritz Lennert
