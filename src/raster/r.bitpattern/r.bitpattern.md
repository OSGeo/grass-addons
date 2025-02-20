## DESCRIPTION

*r.bitpattern* performs bit pattern comparisons. The module can be used
to pixelwise verify a satellite image for low quality pixels if a
Quality Control Bit Index map is provided (e.g. as for MODIS sensor
maps). The functionality is two-fold:

1. define position: set bit(s) to 1 which shall match, then convert
    this position pattern to integer, set pattern= parameter with that
    integer value
2. define pattern \*value\* which should be in that position: first bit
    pattern of value, convert to integer, set patval= parameter

If several bitpatterns have to be tested, the resulting maps can be used
to exclude low quality pixels in the input satellite image using
*r.mapcalc* (OR and NOT operators).

## EXAMPLE

1. Define position:
    
    ```sh
        xx xx 1x xx
        binary: 1000 -> integer: 8 -> pattern=8
    ```
    

2. Define value:
    
    ```sh
        Ex.: We want to check for 0 in that position
        xx xx 0x xx
        binary: 0000 -> integer: 0 -> patval=0
        If value can be arbitrary (0/1), then assume 0 value
    ```
    

## SEE ALSO

*[i.modis.qc](https://grass.osgeo.org/grass-stable/manuals/i.modis.qc.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*

## AUTHORS

Radim Blazek, Markus Neteler
