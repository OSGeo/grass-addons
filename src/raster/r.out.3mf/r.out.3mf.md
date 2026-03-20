## DESCRIPTION

*r.out.3mf* exports an input raster DEM to 3MF format for 3D printing.
The module creates a watertight solid composed of a terrain top surface,
a flat base, and side walls between top and base.

The model extent in XY is scaled so the longest axis matches **size**.
The Z component is shifted to start at **base_height**.

By default, Z differences from the input raster are preserved and scaled by
**zscale**. With **-n**, Z values are normalized to the 0 to 1 range before
**zscale** is applied.

The current computational region is changed only in a temporary local
context while reading and optional resampling are performed.

## NOTES

Null cells are filled using nearest-neighbor interpolation based on a
Euclidean distance transform before meshing.

The **resolution** parameter coarsens the computational region resolution
for export. Larger values reduce triangle count and output file size.

The **-s** flag is reserved for future normal smoothing and is currently
ignored.

## EXAMPLES

Export a DEM at native resolution:

```sh
r.out.3mf input=elevation output=terrain.3mf size=100
```

Export with reduced resolution for faster slicing:

```sh
r.out.3mf input=elevation output=terrain_lowres.3mf resolution=4 size=150
```

Normalize Z before applying scale:

```sh
r.out.3mf input=elevation output=terrain_norm.3mf -n zscale=10
```

## SEE ALSO

*[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html),
[r.out.stl](https://grass.osgeo.org/grass-stable/manuals/addons/r.out.stl.html),
[r.out.vtk](https://grass.osgeo.org/grass-stable/manuals/r.out.vtk.html)*

## AUTHORS

Corey T. White and the GRASS Development Team
