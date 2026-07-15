## DESCRIPTION

*r.vector.ruggedness* represents a measurement of terrain ruggedness
based on the methodology conceived by Sappington et al. (2007). The
measure is calculated by decomposing slope and aspect into 3-dimensional
vectors, and calculating the resultant vector magnitude within a
user-specified moving window size using *r.neighbors*. The user can
specify neighborhood size to measure ruggedness across larger scales.
Neighborhood operations are performed using a rectangular window shape.

## MULTI-SCALE CALCULATION

The *r.vector.ruggedness* tool provides an efficient approach of
calculating the Vector Ruggedness Measure over multiple window sizes.
The *size* argument accepts multiple answers (as a comma separated
list), which will cause the tool to reuse the same slope, aspect and
vector calculations, and apply them to the neighborhood operations that
calculate the vector magnitudes. By default, both the calculation of the
vectors and the vector magnitudes, including over different window sizes
is performed in parallel using all available cores. To restrict parallel
processing, the *nprocs* argument can be changed to use a smaller number
of processing cores. When multiple sizes are used, the *output* raster
name is appended with the window size. Optionally, pre-calculated slope
and aspect maps (in degrees) can be used in the *slope* and *aspect*
arguments to save computational time if the maps are already available.

## NOTES

This script was adapted from the original Sappington et al. (2007)
script.

## EXAMPLE

The examples are to be executed using the GRASS GIS sample North
Carolina data set. To calculate the Vector Ruggedness Measure using a
single neighborhood size:

```sh
    r.vector.ruggedness elevation=elevation size=3 output=vrm
```

For efficient calculations of the Vector Ruggedness Measure over
multiple neighborhood sizes, the slope, aspect and their x, y, z vectors
will be reused during the calculation. The output name will be appended
with the neighborhood size in order to identify the output maps:

```sh
    r.vector.ruggedness elevation=elevation size=3,5,7,9,11 output=vrm
```

## REFERENCES

Sappington, J.M., K.M. Longshore, and D.B. Thomson. 2007. Quantifying
Landscape Ruggedness for Animal Habitat Analysis: A case Study Using
Bighorn Sheep in the Mojave Desert. Journal of Wildlife Management.
71(5): 1419 -1426.

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html)*

## AUTHOR

Steven Pawley
