## DESCRIPTION

*r.object.thickness* evaluates minimum, maximum and mean thickness of
objects of a given category on a raster map.

The thickness is reported both in map units and pixels. The module is
primarly used to estimate the neighborhood window size for filters, such
as those used by
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html)
and [r.fill.category](r.fill.category.md).

Object thickness is evaluated by creating transects along the median
lines of the raster objects, clipping them with object themselves and
evaluating their lengths.

Optionally, *r.object.thickness* can save a CSV file containing the
complete list of the lenghts of the parts of all created transects
inside the objects. It is possible to save a maps containing the median
lines of the objects, in both raster and vector format, a vector map
containing the transects and a vector map containing the clipped
transects.

The *v.transects* addon must be installed to run this module.

## PARAMETERS

The user indicates the category of the objects whose thickness must be
evaluated, and indicating the expected maximum lentgth of the transects
and their spacing.

The expected maximum lentgth of the transects is used to create the
transects before clipping them with the raster objects. It must be
chosen large enough to contain the longer cross secton of the biggest
object. The module issues a warning if the maximum evaluated thickness
is less than or equal to the expected maximum: in this case at least one
transect has not been clipped because it does not intersect the object
boundary. Therefore the expected maximum size parameter must be raised.

Transects spacing controls the distance between transects along the
median line. It must be chosen so that at least one transect is created
on each median line. Smaller values can provide slightly more accurate
results but require more processing time. As a rule of thumb, a good
starting point is setting transects spacing abount 1/50 of the expected
maximum size, but the minimum value can change. If the the transects
spacing value is too low no transect is created and no thickness can be
evaluated: in this case the module issues an error and stops.

It is possibile to choose the direction (N-S or E-W) of the region
resolution used to convert the estimated lenghts in pixels. The choiche
is irrelevant for regions with square cells.

Optional maps containing the median lines of the objects, in both raster
and vector format, the vector map containing the transects and the
vector map containing the clipped transects are created only if a name
is provided for them. In the same way, a CSV file containing the
complete list of the lenghts of the parts of all created transects
inside the objects is also created only if a file name is given.

## EXAMPLE

In this example, the thickness of the water bodies in the *landuse* map
in the North Carolina sample dataset location is evaluated:

```sh
# set the region on the landuse map
g.region rast=landuse@PERMANENT
# evaluate the thickness of water bodies (categoy 6) in the landuse map
# create a vector map containing the median lines called median
# create a vector map containing the transects inside the water bodies called transects_in
r.object.thickness input=landuse@PERMANENT category=6 tsize=4000 tspace=100 vmedian=median itransects=transects_in
```

outputs

```text
Thickness in map units: min 1.525433  max 2962.446155  mean 301.059197
Thickness in pixels: min 0.053524  max 103.945479  mean 10.563481
```

## SEE ALSO

*[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html),
[r.reclass.area](https://grass.osgeo.org/grass-stable/manuals/r.fill.category),
[v.transects](https://grass.osgeo.org/grass-stable/manuals/v.transects),*

## AUTHOR

Paolo Zatelli, DICAM, University of Trento, Italy.
