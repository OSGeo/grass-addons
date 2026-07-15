## DESCRIPTION

*r.rand.weight* generates a binary raster layer with a random selection
of raster cells which are assigned 1. The other cells are assigned NULL
(or optionally 0). The change for a raster cell to get assigned a 1 (to
get selected) depends on the weight (value) of that cell in the input
weight layer.

By default the script is run setting a random seed every time. To ensure
that your results are reproducible you can set the seed value under the
'Sample options' tab. See the 'Random number generator initialization'
in the r.mapcalc helpfile for more details.

You can play with the probability for a cell to be selected by changing
the minimum and/or maximum weights. The script will give a warning if
the user defined minimum \> minimum raster value or if the user defined
maximum is smaller then the maximum raster value. The script will still
run as the user may have set this values intentionally.

You can also set the total number of sample points to be selected using
the under the 'Sample options' tab. This can be done using an absolute
number or as percentage (see the help file of the r.random function for
more details).

## Examples

See the blogpost
[weighted random sample of raster layer](https://pvanb.wordpress.com/2014/05/30/weighted_random_sample_of_raster_layer/)
for examples.

## See also

*[r.random](https://grass.osgeo.org/grass-stable/manuals/r.random.html),
[r.random.cells](https://grass.osgeo.org/grass-stable/manuals/r.random.cells.html)*

## AUTHOR

Paulo van Breugel, paulo at ecodiv.org
