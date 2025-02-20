## DESCRIPTION

*i.edge* is an edge detector based on the Canny edge detection algorithm
\[Canny1986\]. The Canny edge detector is a filter which detects a wide
range of edges in raster maps and produces thin edges as a raster map.

## NOTES

The computational region shall be set to the input map. The module can
work only on small images since the data are loaded entirely into
memory.

### Algorithm

An edge is considered as a change in gradient which is computed from
image digital values. There are two main noticeable differences between
Canny filter and other edge detectors. First, the others algorithm
usually output broad lines (edges) while Canny filter outputs
one-pixel-wide line(s) which represents the most probable edge position
\[Russ2011\]. Second, the Canny filter combines several steps together
while other filters have only one step and often require some pre- or
post-processing to get results which allows further processing. However,
it must be noted that by applying subsequent filters, thresholding and
edge thinning one can get similar results also from other edge
detectors. The implementation used for *i.edge* module is based on code
from \[Gibara2010\].

Canny edge detector is considered as optimal edge detector according to
these three criteria \[Sonka1999\]:

1. important edges cannot be omitted and only actual edges can be
    detected as edges (no false positives);
2. difference in position of the real edge and the detected edge is
    minimal;
3. there is only one detected edge for an edge in original image.

The algorithm consists of a few steps. Firstly, the noise is reduced by
a Gaussian filter (based on normal distribution); the result is smoothed
image. Secondly, two orthogonal gradient images are computed. These
images are combined, so the final gradient can be defined by an angle
and a magnitude (value). Next step is non-maximum suppression which
preserves only pixels with magnitude higher than magnitude of other
pixels in the direction (and the opposite direction) of gradient.
Finally, only relevant or significant edges extracted by thresholding
with hysteresis. This thresholding uses two constants; if a pixel
magnitude is above the higher one (*hT*), it is kept. Pixels with the
magnitude under the lower threshold (*lT*) are removed. Pixels with
magnitude values between these two constants are kept only when the
pixels has some neighbor pixels with magnitude higher than the high
threshold \[Sonka1999\].

### Inputs and parameters

The input is a gray scale image (a raster map). Usually, this gray scale
image is an intensity channel obtained by RGB to HIS conversion. Some
other possibilities include color edges (obtained from RGB color
channels) which may give slightly better results \[Zimmermann2000\]. In
theory, *i.edge* module can be applied not only to images but also to
digital elevation models and other data with abrupt changes in raster
values. The output is a binary raster where ones denote edges and zeros
denote everything else. There are also possible byproducts or
intermediate products which can be part of the output, namely edge
angles (gradient orientations). By changing parameters of the module one
can easily achieve different levels of detail. There are 3 parameters
which affect the result. A `sigma` value and two threshold values,
`low_threshold` (*lT*) `high_threshold` (*hT*). It is recommended to use
*lT* and *hT* threshold values in ratio (computed as *hT/lT*) between 2
and 3 \[Sonka1999\].

## EXAMPLE

```sh
# set the region (resolution) to Landsat image
g.region raster=lsat7_2000_20@landsat

# set the region to experimental area
g.region n=224016 s=220981 w=637589 e=641223

# compute PCA for all Landsat maps for year 2002
i.pca input=`g.list pattern="lsat7_2002*" type=rast sep=,` output_prefix=lsat_pca

# run edge detection on first component
i.edge input=lsat_pca.1 output=lsat_pca_1_edges

# set no edges areas to NULL (for visualization)
r.null map=lsat_pca_1_edges setnull=0
```

## KNOWN ISSUES

Computational region shall be set to input map. The module can work only
on small images since map is loaded into memory. Edge strengths
(gradient values) are not provided as an output but might be added in
the future.

## REFERENCES

  - J. Canny. *A Computational Approach to Edge Detection*. In: IEEE
    Trans. Pattern Anal. Mach. Intell. 8.6 (June 1986), pp. 679–698.
    issn: 0162-8828.
  - J.C. Russ. *The image processing handbook*. CRC, 2011.
  - Tom Gibara. *Canny Edge Detector Implementation*. \[Online; accessed
    20-June- 2012\]. 2010. URL:
    [https://www.tomgibara.com/computer-vision/canny-edge-detector](https://web.archive.org/web/20120628212753/http://www.tomgibara.com:80/computer-vision/canny-edge-detector).
  - M. Sonka, V. Hlavac, and R. Boyle. *Image processing, analysis, and
    machine vision*. PWS Pub. Pacific Grove (1999).
  - P. Zimmermann. *A new framework for automatic building detection
    analysing multiple cue data*. In: International Archives of
    Photogrammetry and Remote Sensing 33.B3/2; PART 3 (2000), pp.
    1063–1070.

## SEE ALSO

*[i.zc](https://grass.osgeo.org/grass-stable/manuals/i.zc.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## AUTHORS

Anna Kratochvilova, Vaclav Petras
