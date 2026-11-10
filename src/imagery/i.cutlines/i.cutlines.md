## DESCRIPTION

*i.cutlines* tiles the images into tiles with irregular borders that
avoid cutting through meaningful objects. This allows tiling an image
for parallel processing while avoiding border effects.

The approach used in *i.cutlines* is inspired by Soares et al (2016).
The module first uses an edge detection algorithm (which the user can
chose with the **edge\_detection** parameter) to identify edges in the
image. It then uses
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html) and
[r.drain](https://grass.osgeo.org/grass-stable/manuals/r.drain) to draw
lines through the image, following edges when possible and going
straight when there are none.

The user can determine the number of lines desired (**number\_lines**)
in each direction and the friction associated with pixels which are not
on an edge detected in the image (**no\_edge\_friction**). The higher
this value, the more the module will follow the detected edges.

In order to avoid that all lines gather into one single lowest cost
path, the module defines a lane for each desired line. The parameter
**lane\_border\_multiplier** defines the a multiplier of the
**no\_edge\_friction** value, in order to define the cost to cross that
line, i.e. the lower the value, the more likely cutlines will join each
other across lanes. Output is in the form of vector polygon tiles. The
user can decide a minimum size defined in map units
(**min\_tile\_size**). Tiles smaller than that size will be merged with
the neighboring tile they share the longest border with.

The user can provide a series of auxiliary vector maps which contain
existing cutlines (roads, boundaries, etc) that the module should take
into account (**existing\_cutlines**). These can be either lines or
polygons. The module will transform all to potential cutlines.

For edge detection the user can chose between the
[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html) module or
the [i.edge](i.edge.md) addon. For the former, the user can determine
the **zc\_threshold** and the **zc\_width** parameters. For the latter,
the **canny\_low\_threshold**, **canny\_high\_threshold** and
**canny\_sigma** parameters. See the manual page of the respective
modules for details about these parameters which might need tuning to
fit to the specific image. As these modules read the entire image into
RAM, *i.cutlines* allows the user to run split the image into
rectangular tiles and to process each tile separately. Tiles can be
defined with the **tile\_width**, **tile\_height** and **overlap**
parameters. If **processes** is higher than one, these tiles will be
processed in parallel as will the
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html) calls
for the two directions.

The **memory** parameter determines the memory used both for the
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html) runs.

## NOTES

Until GRASS GIS version 7.4 included, there was a parameter name
conflict between
[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html) and the
GridModule class in pygrass. For older GRASS GIS versions tiled edge
detection is thus only possible with [i.edge](i.edge.md).

## EXAMPLES

### Zero-crossing edge detection

Using the default
[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html) edge
detection without tiling, default parameters and 10 horizontal and 10
vertical cutlines, creating vector polygon output:

```sh
# ortho photo subarea
g.region raster=ortho_2001_t792_1m n=221070 s=219730 -p
i.cutlines input=ortho_2001_t792_1m number_lines=10 output=ortho_tiles_zc
```

[![image-alt](i_cutlines_default.png)](i_cutlines_default.png)  
Irregular vector tiles created for the NC demo data set orthophoto
(default setting)

### Canny edge detection

Using the
[i.edge](https://grass.osgeo.org/grass-stable/manuals/i.edge.html) Canny
edge detection with tiling and (needed) tile overlap, increased memory,
two parallel processes and 10 horizontal and 10 vertical cutlines,
creating vector polygon output:

```sh
# ortho photo subarea
g.region raster=ortho_2001_t792_1m n=221070 s=219730 -p
i.cutlines input=ortho_2001_t792_1m number_lines=10 edge_detection=canny \
  tile_width=500 tile_height=500 overlap=10 memory=2000 processes=2 output=ortho_tiles_canny
```

[![image-alt](i_cutlines_canny.png)](i_cutlines_canny.png)  
Irregular vector tiles created for the NC demo data set orthophoto
(Canny edge detection)

## REFERENCES

Soares, Anderson Reis, Thales Sehn Körting, and Leila Maria Garcia
Fonseca. 2016. "Improvements of the Divide and Segment Method for
Parallel Image Segmentation." Revista Brasileira de Cartografia 68 (6),
<http://www.lsie.unb.br/rbc/index.php/rbc/article/view/1602>

## SEE ALSO

[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html),
[i.edge](i.edge.md),
[r.tile](https://grass.osgeo.org/grass-stable/manuals/r.tile.html),
[v.mkgrid](https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html),
[i.segment](https://grass.osgeo.org/grass-stable/manuals/i.segment.html)

## AUTHOR

Moritz Lennert
