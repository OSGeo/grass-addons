## DESCRIPTION

*r.wateroutlet.lessmem* is a modified version of
*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*
and requires about one third of memory compared to the original module.
Input drainage direction information is stored as 4-bit segments in the
buffer and output basin result is stored as 1-bit data. Because of heavy
bitwise operations, there may be some performance penalty depending on
the size of the input map. Other than memory management, this module
uses the same interface and algorithm in
*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*,
so please refer to
*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*
for more details.

## SEE ALSO

*[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com)  
based on
[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)
