## DESCRIPTION

The *r.colors.cubehelix* module generates a cubehelix color table and
assigns it to a given raster map if requested. The color table is
generated using *seaborn* Python package. Several parameters are
available to control the cubehelix. When option **map** is specified
*r.colors.cubehelix* assigns the color rules to the given raster map.
The color tables are always stretched based on the range of values of
the map

Depending on the use case, it may be advantageous to use the **-d** to
discretize the color table into intervals.

## NOTES

This module depends on
*[seaborn](https://seaborn.pydata.org/index.html)* which needs to be
installed on your computer. Use your Python package manager (e.g. *pip*)
or distribution package manager to install it.

## EXAMPLES

### Creating a color table as GRASS color rules

We do 0.6 rotation around the axis and use discrete (interval) color
table rather than the standard continuous. If we don't specify output
file, it is printed to standard output:

```sh
r.colors.cubehelix -d ncolors=5 nrotations=0.6
```

```sh
0.000% 218:222:192
20.000% 218:222:192
20.000% 198:166:136
40.000% 198:166:136
40.000% 173:108:112
60.000% 173:108:112
60.000% 119:61:98
80.000% 119:61:98
80.000% 48:28:59
100.000% 48:28:59
```

### Setting color table for a raster map

Now we set several different color tables for the elevation raster map
from the North Carolina sample dataset. We use continuous and discrete
color tables (gradients). The color tables are stretched to fit the
raster map range.

```sh
r.colors.cubehelix -d ncolors=8 nrotations=0.6 map=elevation
```

We can display legend:

```sh
d.legend raster=elevation labelnum=10 at=5,50,7,10
```

Here we set continuous color table with more colors

```sh
r.colors.cubehelix nrotations=1.4 start=4 map=elevation
```

![image-alt](r_colors_cubehelix_two_colors.png)
![image-alt](r_colors_cubehelix.png)

### Setting color table for a vector map

First we create a text file with color rules:

```sh
r.colors.cubehelix -i rot=0.6 output=cubehelix.txt
```

Then we set color table for the vector to the rules stored in a file:

```sh
v.colors map=points rules=cubehelix.txt
```

Color table for 3D raster map can be set in the same way.

## REFERENCES

  - Green, D. A., 2011, [*A colour scheme for the display of
    astronomical intensity
    images*](https://astron-soc.in/bulletin/11June/289392011.pdf),
    Bulletin of the Astronomical Society of India, 39, 289.

## SEE ALSO

*[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html),
[v.colors](https://grass.osgeo.org/grass-stable/manuals/v.colors.html),
[r3.colors](https://grass.osgeo.org/grass-stable/manuals/r3.colors.html),
[r.cpt2grass](r.cpt2grass.md),
[r.colors.matplotlib](r.colors.matplotlib.md)*

seaborn
[cubehelix\_palette](https://seaborn.pydata.org/generated/seaborn.cubehelix_palette.html)
function documentation and an
[example](https://seaborn.pydata.org/examples/palette_generation.html)

## AUTHOR

Vaclav Petras, [NCSU GeoForAll
Lab](httpss://geospatial.ncsu.edu/geoforall/)
