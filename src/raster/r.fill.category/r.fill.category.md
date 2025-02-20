## DESCRIPTION

*r.fill.category* replaces the values of pixels of a given category with
values of the surrounding pixels and stores the output in a new raster
map layer. The module can be used to eliminate one category from a
raster map without leaving areas with NULL values, like for example when
using *r.reclass.area*.

Areas with the given category are eroded and their pixels value is
replaced with the values given by the mode of the surrounding pixels.

*r.fill.category* iteratively applies *r.neighbors* and *r.mapcalc*
until no pixel of the category to replace is left or the maximum number
of iterations is reached.

Optionally, *r.fill.category* can create an MPEG file animating the
replacement process.

## PARAMETERS

The user controls the process by setting the *neighborhood size* in
pixels and the *maximum number of iterations*.

The *neighborhood size* (**nsize**) controls the size of the moving
window where the mode of the values is used to assign a value to the
pixels of the category to be replaced. Large values of the *neighborhood
size* can speed the process considerably but can also lead to unwanted
effects where pixels with the category to remove are mixed with pixels
with different categories. Small values of *neighborhood size* require a
large number of iterations, therefore longer processing times, but
provide better results when categories are mixed.

The *maximum number of iterations* (**maxiter**) is limited to *999*
because the name of the temporary map at each step uses three digits to
identify the iteration.

## INTERMEDIATE MAPS

To save space, maps generated at each iteration are removed as soon as
they are used. It is possible to keep these maps using the **k** flag.

## ANIMATION

If the user provides the name of an MPEG output file, an animation is
created by combining the raster maps of each step.

The **quality** (1-5) parameter controls the quality of the MPEG, lower
values will yield higher quality images, but with less compression (i.e.
larger MPEG file size). Switching from *quality=1* to *quality=5*
reduces the MPEG file size of about 40%, although the actual compression
ratio depends on the number of frames.

The module *r.out.mpeg* is used to generate the MPEG file, therefore the
program mpeg\_encode (aka ppmtompeg) must be available. See *r.out.mpeg*
manual for more information.

If a name for an MPEG output file is provided but the **k** flag is not
set, intermediate maps are kept during the process and deleted after the
MPEG file has been created.

## EXAMPLE

In this example, the lakes in the *landuse* map in the North Carolina
sample dataset location are replaced by categories of the surrounding
pixels:

```sh
# set the region on the landuse map
g.region rast=landuse@PERMANENT
# replace pixels of category 6 (water) with values of the surrounding pixels
# create a drought.mpg animation file in the current directory
r.fill.category input=landuse@PERMANENT output=landuse_dry category=6 animationfile=./drought.mpg
```

It removes all water pixels in 38 iterations. A *drought.mpg* MPEG file
containing the animation of the replacement sequence is created in the
current directory.

## SEE ALSO

*[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html),
[r.reclass.area](https://grass.osgeo.org/grass-stable/manuals/r.reclass.area.html),
[r.out.mpeg](https://grass.osgeo.org/grass-stable/manuals/r.out.mpeg.html),
[r.fill.gaps](r.fill.gaps.md)*

## AUTHORS

Paolo Zatelli and Stefano Gobbi, DICAM, University of Trento, Italy.
