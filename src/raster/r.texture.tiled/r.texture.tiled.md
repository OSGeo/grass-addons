## DESCRIPTION

*r.texture.tiled* cuts a raster input map into tiles and runs
[r.texture](https://grass.osgeo.org/grass-stable/manuals/r.texture.html)
over these tiles before patching the result together into a single
output raster map.

The overlap between tiles is calculated internally in order to
correspond to the window **size** in order to avoid any border effects.

Tiles can be defined with the **tile\_width**, **tile\_height** and
**overlap** parameters. If **processes** is higher than one, these tiles
will be processed in parallel.

The **mapset\_prefix** parameter allows to make sure that the temporary
mapsets created during the tiled processing have unique names. This is
useful if the user runs *r.texture.tiled* several times in parallel
(e.g. in an HPC environment).

## NOTES

The parameters for texture calculation are identical to those of
[r.texture](https://grass.osgeo.org/grass-stable/manuals/r.texture.html).
Currently, this module only allows calculating one texture feature at a
time. The **n** flag allowing null cells is automatically set in order
to avoid issues at the border of the current computational region / of
the input map.

## EXAMPLE

Run r.texture over tiles with size 1000x1000 using 4 parallel processes:

```sh
g.region rast=ortho_2001_t792_1m
r.texture.tiled ortho_2001_t792_1m output=ortho_texture method=idm \
   tile_width=1000 tile_height=1000 processes=4
```

## SEE ALSO

[r.texture](https://grass.osgeo.org/grass-stable/manuals/r.texture.html)

## AUTHOR

Moritz Lennert
