## DESCRIPTION

*r.houghtransform* is performing vector line extraction from edges, or
generally any raster lines, in a raster map using the Hough transform.
An edge is considered as potential line feature previously detected by
some other algorithm represented by value 1 in the raster map.

In general, the Hough transform is a method for finding geometry
structures in images. This module uses the Hough transform for straight
line detection. Extracted line segments can be used to construct
rectangles or generally any other polygons. The transformation itself
creates a raster image which is then used for finding line segments. The
input of Hough transform is an image which contains only edges, or
generally any lines, represented as raster map. It is not necessary but
for practical reasons, these edges or lines should be thin e.g., those
produced
*[r.thin](https://grass.osgeo.org/grass-stable/manuals/r.thin.html)*
module or by *[i.edge](i.edge.md)* module (Canny edge detector).

### Algorithm

Lines can be mathematically represented in many ways. For this module,
the following representation was chosen. Line is represented in polar
coordinates where *r* is the distance between the line and the origin
and *Θ* is the angle of the vector from the origin to the closest point.
The equation follows.

*r* = *x* cos(Θ) + *y* sin(Θ)

When applying Hough transformation for streight lines, the point in the
original image leads to a sinusoidal curve in the transformed image.
Points in the original image belonging to one line result in sinusoids
intersecting in one point in the transformed image (Hough space). The
coordinates of this point describe the parameters *r*, *Θ* of the line
and its value represents the number of points of the line.

In other words, points from the original image with *x* and *y* axes are
transformed into the Hough space with *r* and *Θ* axes. We can say that
the resulting (transformed) image is the Hough image. One point (pixel)
in the original image is represented by a curve in the Hough image and
one point in the Hough image defines a line in the original image by *r*
and *Θ* parameters. One line in the original image is represented by an
intersection of curves. More points (pixels) in one line lead to a
higher value in the point of curves' intersection.

For further evaluation, it is necessary to extract local maximum values
from the Hough image which correspond to significant lines of the
original image. This way we obtain the desired lines in form of *r*, *Θ*
coordinate pairs. However, we do not obtain the end coordinates of the
original line segment (*r*, *Θ* are line parameters).

To extract significant lines from Hough image, *r.houghtransform* module
uses the *identify and remove* Hough transform method described in
\[Fiala2003\]. As mentioned above, it is needed to extract the local
maxima representing the lines from the result of the Hough image. This
task is compliated by the because presence of noise in the original
image. The *identify and remove* Hough transform method provides not
just the line parameters but also the actual coordinates of points as a
byproduct. It is based on the idea of sequential removing peaks from the
transformation result and eliminating the effect caused by the points of
original image belonging to the removed peak.

Lines obtained by *identify and remove* Hough transform method had to be
processed in order to get the actual line segments from the original
image. Due to the noise in the original image, certain points can be
included in the detected line although they do not belong to it. The
subsequent step — extraction of line segments — has to ignore the
outlying pixels. However, the main goal is to find separate line
segments (pixels belonging to one line segment), so that the line
segment is not interrupted. The method needs to tolerate also small gaps
because some line segments can actually be interrupted, e.g. by
vegetation. On the other hand, these gaps cannot be too frequent because
many interruptions would indicate line segments which are probably not
part of the feature. The serious line interruption means that there are
two segments on one line in the image. As a result, the produced output
can be more than one line segment for one detected line.

The Hough transform can be optimized by providing directions of edges
\[Galambos2000\] (possible result of the Canny edge detector or other
edge detection algorithm). These angles are used to search only pixels
which are in the direction of the particular line. The
*r.houghtransform* module uses exactly this approach.

It must be noted that line segment reconstruction does not have to be
considered as a part of Hough transformation. The basic result of Hough
transformation is the transformed image (Hough image). Thus,
*r.houghtransform* module provides the posibilty to export also this
image.

However, for implementation of the *identify and remove* Hough transform
method, it is necessary and also very advantageous to create data
structures instead of an image because of the need for backtracking the
lines to the original image. As a result, *r.houghtransform* module
combines Hough transformation and its *identify and remove* extension,
so that the primary result are the line segments.

From the transformed image (Hough image), we can infer certain rules and
symmetries, e.g. four peeks at certain positions may denote a rectangle.
So possibly, some algorithms can use the Hough image to detect features
in different ways than *identify and remove* Hough transform method.
However, these algorithms are not part of *r.houghtransform* module,
just the Hough image is provided.

### Inputs and outputs

The main purpose of the module is to detect line segments, so the output
is a vector map which contains line segments found in the input raster
edge map. The level of details is controlled by several parameters. The
continuous straight series of pixels are interpreted as a part of a line
when they are not too scattered (thus possible line width or line
inaccuracy is limited). The algorithm tolerates small and not too often
repeated gaps. As a result, the *r.houghtransform* module can produce
more than one line segment for one detected line when the gap is too
long. All the limits mentioned above as well as the minimum length of
line segment can also be controlled by the user as well as the
approximate number of all resulting lines.

The edge directions (e.g. the optional output of *[i.edge](i.edge.md)*)
can serve as an additional input to *r.houghtransform* module. The
availability of edge directions reduces significantly the time needed
for the computation without any negative effect on the result.

The optional output of *r.houghtransform* module is the image
transformed into the Hough space (Hough image), i.e. the original output
of the Hough transformation. It can be used for further processing and
analysis if desired. The image is outputted as a raster map at
coordinates (0,0). One image pixel is represented as one cell but the
image does not have any geographical meaning (it is in Hough space).
Note that Hough image does not contain all the information which is used
to construct line segments (namely, the backtracking information). The
color table of this image is set to gray scale with the black
representing a zero. Note that the number of curves in this image is
significantly reduced when you provide angle map as an optional input.
So, if you want to get nicely looking image, you shall not provide angle
map to *r.houghtransform* module.

## SEE ALSO

*[r.thin](https://grass.osgeo.org/grass-stable/manuals/r.thin.html)*,
*[i.edge](i.edge.md)* (in GRASS Addons)

## REFERENCES

  - M. Fiala. *Identify and Remove Hough Transform Method*. In: Proc.
    Vision Interface. 2003, pp. 184-187. url:
    <http://www.cipprs.org/papers/VI/VI2003/papers/S5/S5_fiala_28.pdf>.
  - C. Galambos, J. Kittler, and J. Matas. *Using gradient information
    to enhance the progressive probabilistic Hough transform*. In:
    Pattern Recognition, 2000. Proceedings. 15th International
    Conference on. Vol. 3. IEEE. 2000, pp. 560-563.

## AUTHORS

Anna Kratochvilova, Vaclav Petras
