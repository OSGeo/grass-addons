## DESCRIPTION

*r.bearing.distance* computes the bearing and/or straight-line distance
from a point location to all non-NULL cells in a raster map. Optionally,
the bearing returned in each non-NULL cell may be:

- the actual bearing measured from the point location;
- the difference between that bearing and a reference bearing;
- one of two measures of the extent to which the bearing is or is not
    orthogonal to the reference bearing.

By default, the **bearing** map records the bearing of a straight line
projected from the point location to each non-NULL cell in the input
map. If the **-r** flag is set then this map records the reverse
bearing, i.e. that of a straight line projected from each non-NULL cell
towards the point location. The point location itself is coded NULL,
irrespective of whether it was NULL or non-NULL in the input map.

If a **reference\_bearing** is specified without the **-a** or **-b**
flags then the bearing map will by default record the bearing relative
to the reference bearing. This relative bearing is the clockwise
difference between the reference bearing and the bearing that would
otherwise have been recorded. For example: if the bearing is 315 degrees
and the reference bearing 270 degrees, the relative bearing would be +45
degrees; if the bearing is 45 degrees and the reference bearing 270
degrees, the relative bearing would be +135 degrees.

If a **reference\_bearing** is specified along with the **-a** flag then
the bearing map will record the bearing relative to an axis defined by
the reference bearing, such that if the bearing is aligned (or 180
degrees opposite) the reference bearing the difference will be zero
degrees, and if it is orthogonal the difference will be +90 degrees.

If a **reference\_bearing** is specified along with the **-b** flag then
the bearing map will record the signed bearing relative to an axis
defined by the reference bearing, such that if the bearing is aligned
(or 180 degrees opposite) the reference bearing the difference will be
zero degrees, if it is orthogonal in a clockwise direction the
difference will be +90 degrees, and if it is orthogonal in an
anticlockwise direction the difference will be -90 degrees.

The **distance** map records the straight-line distance from the point
location to each non-NULL cell in the input map. The distance is
computed using the geographic coordinates of the point location and the
geographic coordinates of the centre of each non-NULL map cell.

The **segment** map records which azimuthal segment the bearing (or
relative bearing) falls in. The **-e** flag determines whether 4 or 8
segments are returned. The **-s** flag determines whether segments are
centred on a bearing (or relative bearing) of zero degrees, or start
clockwise from zero degrees.

The **csv\_seg** file is a plain text CSV file which records the count
and percentage of cells falling in each of the segments.

The **csv\_ax** file is only available if an axial relative bearing has
been requested by setting the **-a** or **-b** flags. In the case of an
axial relative bearing (**-a**) this plain text CSV file records the
count of cells whose relative bearing (θ) falls in each of 5 ranges: θ =
0; 0 \< θ ≤ 22.5; 22.5 \< θ ≤ 45; 45 \< θ ≤ 67.5; 67.5 \< θ ≤ 90. It
also records the mean value of θ. In the case of a signed axial relative
bearing (**-b**) this file distinguishes positive and negative values of
θ. It also records separate means and standard deviations of the
positive and negative values of θ in addition to an overall mean and
standard deviation.

## NOTES

This module was originally written for an archaeological investigation
of the orientation of viewsheds from prehistoric burial mounds, but it
will be useful for visibility analysis in a range of academic
disciplines, as well as planning and environmental management. Indeed,
it potentially has applications for any kind of analysis which involves
a set of non-NULL cells that are somehow related to a point location.

In the case of visibility analysis, the **-r** flag will be particularly
useful when a viewshed has been produced with observer and target
offsets set so as to compute the visibility from each cell back towards
the point location set as the 'viewpoint'. With the **-r** flag the
bearing returned will similarly be that from each cell in the viewshed
back towards the point location of interest.

The code does not currently deal with Lat/Long databases.

The module only runs when the current region has integer resolution
(since the algorithm is not robust in cases where resolution is
non-integer). The code might work satisfactorily when the map resolution
in non-integer, but this has not been rigorously checked.

## REFERENCES

- Harris, B. and Lake, M. (in prep.) The influence of visibility on
    the territorial packing of Neolithic long barrows in central
    southern England. For submission to *Journal of Archaeological
    Method and Theory*.

## SEE ALSO

*[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)*

## AUTHOR

Mark Lake, UCL Institute of Archaeology, University College London, UK.
(the author).

## ACKNOWLEDGEMENTS

Functionality developed in consultation with Barney Harris, UCL
Institute of Archaeology, University College London, UK.
