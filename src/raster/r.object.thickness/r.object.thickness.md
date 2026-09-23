## DESCRIPTION

*r.object.thickness* evaluates the minimum, maximum, and mean thickness of
objects of a given category on a raster map.

The thickness is reported both in map units and pixels. The module is primarily
used to estimate the neighborhood window size for filters, such as those used by
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html) and
[r.fill.category](https://grass.osgeo.org/grass-stable/manuals/addons/r.fill.category.html).

Another use case is to estimate the width of small landscape elements (SLE),
e.g., to complement statistics computed by
[r.object.geometry](https://grass.osgeo.org/grass-stable/manuals/r.object.geometry.html)

Object thickness is evaluated by creating transects along the median lines of
the raster objects, clipping them with objects themselves, and evaluating their
lengths. This is done using the *v.transects* addon, which must therefore
be installed to run this module.

Optionally, *r.object.thickness* can save a CSV file containing the complete
list of the lengths of the parts of all created transects inside the objects. It
is possible to save a vector map containing the transects, a vector map
containing the clipped transects and maps containing the median lines of the
objects, in both raster and vector format. The attribute table of the latter
contains the average, minimum, and maximum widths of the transects within the
objects.

## PARAMETERS

The user must indicate the category of the objects whose thickness should
be evaluated, as well as the expected maximum length of the transects and
their spacing.

The expected maximum length of the transects is used to create the transects
before clipping them with the raster objects. It must therefore be large enough
to contain the longer cross section of the biggest object. The module issues a
warning if the maximum evaluated thickness is less than or equal to the expected
maximum: in that case, at least one transect has not been clipped because it
does not intersect the object boundary. Therefore, the expected maximum size
parameter must be raised.

Transect spacing controls the distance between transects along the median line.
It must be chosen so that at least one transect is created on each median line.
Smaller values can provide slightly more accurate results but require more
processing time. As a rule of thumb, a good starting point is setting transects
spacing around 1/50 of the expected maximum size, but the minimum value can
change. If the transects spacing value is too low, no transect is created and no
thickness can be evaluated: in that case, the module issues an error and stops.

It is possible to choose the direction (N-S or E-W) of the region resolution
used to convert the estimated lengths in pixels. The choice is irrelevant for
regions with square cells.

By default, the transect spacing is measured as straight distances between the
transects (default) or along the line. This is set by the **metric** parameter.
In addition, the parameter **transect_perpendicular** determines whether the
transects are generated perpendicular to either the input line or to the line
connecting the transect points. See the manual page of
[v.transects](https://grass.osgeo.org/grass-stable/manuals/addons/v.transects.html)
for more details.

Optional maps containing the median lines of the objects, in both raster and
vector format, the vector map containing the transects, and the vector map
containing the clipped transects are created only if a name is provided for
them. In the same way, a CSV file containing the complete list of the lengths of
the parts of all created transects inside the objects is also created only if a
file name is given.

## EXAMPLE

In this example, the width of the water bodies in the *landuse* map in the North
Carolina sample dataset is evaluated:

```sh
# set the region on the landuse map
g.region rast=landuse@PERMANENT
# evaluate the thickness of water bodies (category 6) in the landuse map
# create a vector map containing the median lines called median
# create a vector map containing the transects inside the water bodies
# called transects_in
r.object.thickness input=landuse@PERMANENT category=6 tsize=4000 tspace=100 \
vmedian=median itransects=transects_in
```

outputs

```text
Thickness in map units: 
min = 1.525433 
max = 2962.446155 
mean = 301.059197

Thickness in pixels: 
min = 0.053524
max = 103.945479
mean = 10.563481
```

## SEE ALSO

*[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html),
[r.reclass.area](https://grass.osgeo.org/grass-stable/manuals/r.fill.category),
[v.transects](https://grass.osgeo.org/grass-stable/manuals/v.transects)*

## AUTHOR

- Paolo Zatelli, DICAM, University of Trento, Italy (original version)
- Paulo van Breugel, HAS green academy, Netherlands (add stats to generated
vector layers).
