## DESCRIPTION

*v.what.spoly* queries vector map with overlaping "spaghetti" polygons
(e.g. Landsat footprints) at given location. Polygons must have not
intersected boundaries (not cleaned).

## NOTES

Module only runs in locations with Cartesian coordinates. Module needs
GDAL utilities and GDAL-Python to be installed.

## EXAMPLES

```sh
    v.what.spoly.py input=poly out=poly_select coor=465113.204082,5436513.2449
```

## SEE ALSO

*[v.what](https://grass.osgeo.org/grass-stable/manuals/v.what.html)*

## AUTHOR

Alexander Muriy (IEG RAS, Moscow)
