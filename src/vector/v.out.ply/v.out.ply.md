## DESCRIPTION

*v.out.ply* converts a GRASS vector map in binary format to an ASCII
file in PLY format. Currently supported is points export only.
*v.out.ply* is designed for large point clouds and fairly fast if only
coordinates are exported. The export of attributes with the option
**columns** can slow down the export considerably.

If the **output** parameter is not given then the coordinates of any
*point* data within the vector map is sent to stdout.

## REFERENCES

<https://paulbourke.net/dataformats/ply>  
<https://sites.cc.gatech.edu/projects/large_models/ply.html>

## SEE ALSO

*[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html),
[v.in.ply](v.in.ply.md)*

## AUTHOR

Markus Metz  
based on
[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html)
