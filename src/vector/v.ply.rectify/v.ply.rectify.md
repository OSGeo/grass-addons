## DESCRIPTION

*v.ply.rectify* imports a PLY point cloud, georeferences and exports it.
The first three vertex properties must be the x, y, z coordinates with
property names "x", "y", "z", in this order.

A text file with Ground Control Points (GCPs) must exist in the same
folder where the point cloud is located, and the textfile must have the
same name like the point cloud, but ending on .txt instead of .ply.

The text file with GCPs must have the following format with one GCP per
line:

```sh
  x y z east north height status
```

with *x, y, z* as source coordinates and *east, north, height* as target
coordinates. The *status* indicates whether to use a GCP (status is not
zero) or not (status is zero). Entries must be separated by whitespace
or tabs. Decimal delimiters must be points.

The georecitifictation method used is a 3D orthogonal rectification
where angles are preserved. 3D objects are shifted, scaled and rotated,
but no shear is introduced. Please read the output of the module, in
particular the root mean square (RMS) errors.

*v.ply.rectify* optionally exports the georeferenced point cloud not
only with real coordinates, but also with shifted coordinates (*-s*
flag) for display in meshlab or similar software that can not deal with
real coordinates. The exported PLY point clouds will be in the same
folder like the input PLY point cloud.

## EXAMPLE

With a point cloud file *pointcloud.ply* and associated control points
in *pointcloud.txt*,

```sh
v.ply.rectify -s input=pointcloud.ply
```

will generate three files: *pointcloud\_georef.ply* with the
georeferenced point cloud, *pointcloud\_georef\_shifted.ply* with the
georeferenced point cloud shifted to the coordinates' center, and
*pointcloud\_rms.csv* with the RMS errors of the control points.

## SEE ALSO

*[v.in.ply](v.in.ply.md), [v.out.ply](v.out.ply.md),
[v.rectify](https://grass.osgeo.org/grass-stable/manuals/v.rectify.html),
[v.transform](https://grass.osgeo.org/grass-stable/manuals/v.transform.html)*

## AUTHOR

Markus Metz
