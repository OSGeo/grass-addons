## DESCRIPTION

*i.points.auto* tries to automatically generate a given number of new
ground control points (GCPs) by matching the input map to a target map
through FFT correlation, based on a few existing ground control points,
previously defined by the user, for example through the [Ground Control
Points
Manager](https://grass.osgeo.org/grass-stable/manuals/wxGUI.gcp.html).
The goal of the module is thus to automaticallty increase the number of
control points to enable higher quality geocoding of imagery to a master
image (co-registration).

## NOTES

It is recommended to use maps filtered with the DIVERSITY or STDDEV
filters of the *r.neighbors* module, with a window size of 3x3 or 5x5
pixels. However, the algorithm sometimes works well also with the
original maps. The produced GCPs can then be used on the original
imagery.

The actual number of newly generated ground control points will likely
be less than the given maximum number of ground control points because
each generated point is filtered using its FFT correlation coefficient,
and optionally also by the given RMS threshold.

*i.points.auto* supports the usual transformation orders 1-3 and
requires the corresponding number of previously set ground control
points: 3 for order 1, 6 for order 2, 10 for order 3.

## SEE ALSO

The GRASS 4 *[Image Processing
manual](https://grass.osgeo.org/gdp/imagery/grass4_image_processing.pdf)*

*[i.group](https://grass.osgeo.org/grass-stable/manuals/i.group.html),
[i.rectify](https://grass.osgeo.org/grass-stable/manuals/i.rectify.html),
[i.target](https://grass.osgeo.org/grass-stable/manuals/i.target.html),
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html),
[Ground Control Points
Manager](https://grass.osgeo.org/grass-stable/manuals/wxGUI.gcp.html)*

## REFERENCE

(note that the former module name was **i.coregister**)

- Neteler, M, D. Grasso, I. Michelazzi, L. Miori, S. Merler, and C.
    Furlanello (2005). An integrated toolbox for image registration,
    fusion and classification. International Journal of Geoinformatics,
    1(1):51-61
    ([PDF](https://neteler.org/wp-content/uploads/neteler/papers/neteler2005_IJG_051-061_draft.pdf))

## AUTHORS

Ivan Michelazzi  
Luca Miori  
Markus Metz
