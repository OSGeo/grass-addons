## DESCRIPTION

*r.out.3mf* exports an input raster DEM to **3MF** or **STL** format for
3D printing. By default the module creates a watertight solid composed of a
terrain top surface, a flat base, and side walls between the top and base.

The model extent in XY is scaled so the longest axis matches **size** (in mm),
preserving the geographic aspect ratio of the input region. The terrain is
lifted so it starts at **base_height** mm above the base.

By default, Z differences from the input raster are preserved and scaled by
**zscale**. With the **-n** flag, Z values are normalized to the 0 to 1 range
before **zscale** is applied, in which case **zscale** is interpreted directly
as the millimeters of relief. This is useful for non-metric or unitless DEMs.

By default the current computational region (extent and resolution) is
respected, so the export covers exactly the area set with *g.region*. Use the
**-r** flag to export the full extent of the input raster instead. Any region
change, including the **resolution** coarsening, is made within a temporary
region, so the user's region is restored when the tool finishes.

## NOTES

Null cells are filled with *r.fillnulls* spline interpolation into a temporary
raster (removed on exit) before meshing, so the resulting mesh is watertight.

The **resolution** parameter coarsens the computational region resolution for
export. A value of `1` uses the native resolution; larger values reduce the
triangle count and output file size.

With **format=stl** the output is a binary STL, which is geometry-only and
universally supported by slicers but carries no color. With **format=3mf** the
output is a 3MF package that can embed per-triangle color when **colors** is
set to `elevation`; rendering those colors requires a multi-material slicer.
When **colors=elevation** is combined with **format=stl**, the color request is
ignored and a warning is issued.

The **-m** flag produces a hollow mold: an open-bottom shell with outer walls,
inner walls offset inward by **wall_thickness**, and a sealed bottom rim. This
is intended for kinetic-sand impressions or casting molds rather than a solid
display model.

The output file extension is forced to match **format** regardless of the name
supplied in **output**.

## EXAMPLES

Export a DEM as a solid 3MF model at native resolution:

```sh
r.out.3mf input=elevation output=terrain.3mf size=100
```

Export with reduced resolution for faster slicing:

```sh
r.out.3mf input=elevation output=terrain_lowres.3mf resolution=4 size=150
```

Export the full input raster extent regardless of the current region:

```sh
r.out.3mf input=elevation output=terrain.3mf -r size=120
```

Normalize Z and set 10 mm of relief:

```sh
r.out.3mf input=elevation output=terrain_norm.3mf -n zscale=10
```

Export a hollow mold for kinetic sand:

```sh
r.out.3mf input=elevation output=mold.3mf -m wall_thickness=4 base_height=5
```

Export a geometry-only STL:

```sh
r.out.3mf input=elevation output=terrain.stl format=stl size=120
```

## SEE ALSO

*[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html),
[r.out.gdal](https://grass.osgeo.org/grass-stable/manuals/r.out.gdal.html),
[r.out.stl](https://grass.osgeo.org/grass-stable/manuals/addons/r.out.stl.html),
[r.out.vtk](https://grass.osgeo.org/grass-stable/manuals/r.out.vtk.html)*

## AUTHORS

Corey T. White and the GRASS Development Team
