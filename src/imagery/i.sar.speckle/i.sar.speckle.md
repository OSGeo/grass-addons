## DESCRIPTION

A simple procedure to reduce speckle noise in SAR images.

So far, the only algorithm implemented is the Lee filter. So, the
*method* parameter is set to *lee* by default.

The *size* parameter is the one used in
[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html)
and is used to calculate local mean and local square mean. It must be
odd.

## REFERENCES

Lee, J. S. (1986). Speckle suppression and analysis for synthetic
aperture radar images. Optical engineering, 25(5), 255636.

## SEE ALSO

[r.neighbors](https://grass.osgeo.org/grass-stable/manuals/r.neighbors.html)

## AUTHOR

Margherita Di Leo
