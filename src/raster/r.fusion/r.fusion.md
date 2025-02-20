## DESCRIPTION

*r.fusion* enhances the resolution of a raster map by using spatial
detail of a high-resolution map. The actual values in the resultant
output map correspond to the input map while the spatial detail
corresponds to the high-resolution map. The effect is similar to
pan-sharpening, but the method can be applied more generally, not only
to imagery but also to climatological data such as temperature or
precipitation.

## NOTES

Two different methods are available with the **method** option:
*difference* and *proportion*.

The *difference* method uses the formula

A - B + B = A

more specifically

highres(A<sub>lowres</sub> - B<sub>lowres</sub>) + B<sub>highres</sub> =
A<sub>highres</sub>

where *highres()* is a function to interpolate the differences. Here,
*r.resamp.filter* is used for interpolation.

The *proportion* method is suitable for e.g. precipitation where zero
precipition must stay zero precipition, and uses the formula

A / B \* B = A

more specifically

highres(A<sub>lowres</sub> / B<sub>lowres</sub>) \* B<sub>highres</sub>
= A<sub>highres</sub>

Again, *highres()* is a function to interpolate the proportions, and
*r.resamp.filter* is used for interpolation. For the *proportion*
method, all values in the high-resolution B map must be \> 0.

## SEE ALSO

*[r.resamp.filter](https://grass.osgeo.org/grass-stable/manuals/r.resamp.filter.html)*

## AUTHOR

Markus Metz, mundialis
