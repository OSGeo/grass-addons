## DESCRIPTION

*r.skyline* takes a viewshed map as input and analyses the horizon. It
has two main functions:

1. Given 2 viewshed maps containing inclination values it can determine
    whether the original viewpoint appears below, on, or above the
    horizon when viewed from each cell that falls in the viewshed (see
    below for important information about how the viewsheds should be
    calculated in order to support this function);
2. More generally, given any single viewshed map in which cells are
    coded either NULL (not visible from the viewpoint) or non-NULL
    (visible) it identifies cells that fall on 'near' or 'far' horizons
    (see **edges**), and determines which of those cells may not truly
    fall on the real horizon because they are on the edge of the
    computational region or fall at the maximum viewing distance
    specified when creating the original viewshed.

*r.skyline* can output up to 5 raster maps and 1 plain text CSV file, as
described here.

The **skyline\_index** map records, for each cell in the viewshed, the
difference between the inclination of the line-of-sight from that cell
back towards the viewpoint and the inclination of the line-of-sight from
the viewpoint towards the point on the horizon opposite the cell in
question. If this skyline index is positive, then the viewpoint would
appear to be raised above the skyline, whereas if it is negative then it
would appear below the skyline. This option requires two input viewshed
maps, **viewshed** and **viewshed2**, which must both record inclination
values (the default output from *r.viewshed* and the only ouput from the
older *r.los*). Note that the validity of the skyline index depends upon
the user setting appropriate observer (viewpoint) and target offsets
when creating the input viewsheds - see NOTES for important information
about how to use this function.

The **hoz\_azimuth** map identifies the cells that fall on the horizon
and records the azimuth at which they appear from the viewpoint. The
horizon depicted on this map may include cells that occur at the maximum
viewing distance from the viewpoint and/or at the edge of the current
region. Since such cells may not really represent the point beyond which
no more land is visible it may be prudent, depending on the purpose of
the analysis, to generate a **hoz\_type** map.

The **hoz\_inclination** map identifies the cells that fall on the
horizon and records additional data derived from the input viewshed map.
If that map was computed with
*[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)*
then the **hoz\_inclination** map will record either the inclination
(*r.viewshed* default), simply '1' meaning that the cell was visible
(*r.viewshed* **-b** flag), or the elevation difference between the
viewpoint and horizon cell (*r.viewshed* **-e** flag). If the input
viewshed map was computed with the older*[r.los](r.los.md)* then the
**hoz\_inclination** map will record the inclination at which the
horizon cells appear from the viewpoint. Note that in all cases the
horizon depicted on this map may include cells that occur at the maximum
viewing distance from the viewpoint and/or at the edge of the current
region. Since such cells may not really represent the point beyond which
no more land is visible it may be prudent, depending on the purpose of
the analysis, to generate a **hoz\_type** map.

The **hoz\_type** map records the kind of horizon represented by each
horizon cell. This distinguishes horizon cells as follows:

- 1 = cell falls on true far horizon;
- 2 = cell falls at maximum viewing distance;
- 3 = cell falls at edge of current region.
- NULL = cell does not fall on the horizon (or falls on the original
    viewpoint).

Note that type 1 horizon cells might not really fall on the true horizon
if increasing the maximum viewing distance used when calculating the
viewshed would also increase the viewshed size. Type 2 and 3 horizon
cells might or might not fall on the true horizon - there is no way for
this module to determine that.

The **edges** map records all viewshed edges, which may be of interest
when the viewshed in not contiguous (i.e. there is more than one 'patch'
of visible land). In this case a marked cell may represent one of the
following: the point at which land becomes visible; the point at which
land becomes temporarily invisible before becoming visible again; the
point beyond which no more land is visible. We refer to case 2 as a
'near horizon' and case 3 as a 'far horizon'. The **hoz\_azimuth**,
**hoz\_type** and **hoz\_inclination** maps, and the **profile** only
record 'far horizon' cells. The **edges** map uses the same coding
scheme as the **hoz\_type** map.

The plain text CSV file **profile** records various properties of the
'far' horizon cells. This is sorted by increasing azimuth, so is useful
for plotting horizon profiles clockwise from North.

## NOTES

In order to use *r.skyline* it is necessary to know the coordinates of
the viewpoint and the maximum viewing distance specified when computing
the input viewshed(s). **coordinate** and **max\_dist** should be set to
these values.

It is *important to understand* that the validity of the skyline index
requires careful consideration of the observer (viewpoint) and target
offsets used to create the two input viewshed maps. *r.skyline* supports
the use of 2 different viewshed maps to ensure that the correct
inclination values are used for the horizon and line-of-sight back
towards the 'viewpoint'. The following example explains how these may be
used. Suppose you wish to calculate the skyline index for all locations
in the landscape from which a 3m high building is visible, in other
words whether the top of that building appears above, on or below the
horizon behind it. There are three steps:

1. Compute the viewshed that will be used to calculate the inclination
    of the line-of-site to the horizon from the top of the building
    (**viewshed**). This would be achieved by treating the building as
    the viewpoint and setting the viewpoint offset (height above the
    ground of the viewing position) to the height of the building (3m)
    and the target offset (height above the ground of whatever the
    viewer is looking at) to zero.
2. Compute the viewshed that will be used to calculate the inclination
    of the line-of-sight towards the building from all locations from
    which it can be seen (**viewshed2**). This would be achieved by
    swapping appropriate viewpoint and target offsets to ensure that the
    visibility module computes the correct line-of-sight, so in this
    case we would set the viewpoint offset to the height of the building
    (3m) and the target offset to the height of a person looking at the
    building (say 1.75m).
3. Finally, use *r.skyline* to compute the skyline index by specifying
    **viewshed** and **viewshed2** as the input viewsheds. Be sure also
    to set **coordinate** and **max\_dist** to the values that were used
    to generate the two input viewsheds.

The code does not deal with Lat/Long databases.

The module only runs when the current region has integer resolution
(since the algorithm is not robust in cases where resolution is
non-integer).

## REFERENCES

- Harris, B. and Lake, M. (in prep.) The influence of visibility on
    the territorial packing of Neolithic long barrows in central
    southern England. For submission to *Journal of Archaeological
    Method and Theory*.

## SEE ALSO

*[r.bearing.distance](r.bearing.distance.md)*, *[r.los](r.los.md)*,
*[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)*.

## AUTHOR

Mark Lake, UCL Institute of Archaeology, University College London, UK
(the author).

## ACKNOWLEDGEMENTS

Uses mergesort algorithm from R. Sedgewick, 1990, *Algorithms in C*,
Reading, MA: Addison Wesley.

The skyline index emerged out of conversations with Barney Harris, UCL
Institute of Archaeology, University College London, UK.
