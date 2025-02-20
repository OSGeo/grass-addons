## DESCRIPTION

*r.findtheriver* finds the nearest stream pixel to a coordinate pair
using an upstream accumulating area (UAA) raster map. This is necessary
because the coordinates for streamflow gages are often not perfectly
registered to the topography represented by a digital elevation model
(DEM) map. This presents a problem when trying to derive a watershed
contributing area using
*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*;
if the streamflow gage does not fall on the stream as represented in the
DEM,
*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*
can fail to derive the watershed area.

The basic assumption is that the UAA for "stream" pixels will be much
higher than for adjacent "non-stream" pixels. *r.findtheriver* attempts
to "snap" the coordinates of the streamflow gage to the "true" stream
location by first identifying stream pixels within a search window, and
then selecting the stream pixel that is closest (Cartesian distance) to
the input gage coordinates. Stream pixels are identified by searching
the UAA raster window for pixels that exceed a threshold. This is done
by computing the log10 of the UAA value for the pixel corresponding to
the gage coordinates and subtracting from it the log10 of each pixel in
the window; for a given pixel if this difference is greater than the
threshold, the pixel is deemed to be a stream pixel.

*r.findtheriver* will automatically compute the window and threshold if
they are not supplied by the user. The window is determined based on a
THRESHOLD\_DISTANCE / cell resolution of the UAA map. The threshold is
determined by subtracting the log10 of the UAA value at the input gage
coordinate from the log10 of the maximum UAA value of the map, and then
rounding down to the nearest integer, in other words: threshold = floor(
log(maxUAA) - log(gageUAA) ).

The closest stream pixel is printed to standard output. If no stream
pixels were found, nothing is printed.

## SEE ALSO

*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*

## AUTHORS

[Brian Miles](mailto:brian_miles@unc-edu)  
Updated to GRASS 7 by [Huidae Cho](mailto:grass4u@gmail-com)
