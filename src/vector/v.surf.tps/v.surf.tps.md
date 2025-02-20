## DESCRIPTION

*v.surf.tps* performs multivariate thin plate spline interpolation with
regularization. The **input** is a 2D or 3D vector *points* map. Values
to interpolate can be the z values of 3D points or the values in a
user-specified attribute column in a 2D or 3D vector map. Output is a
raster map. Optionally, several raster maps can be specified to be used
as covariables which will improve results in areas with few points. The
module can be regarded as a combination of a multiple regression and
spline interpolation.

The **min** options specifies the minimum number of points to be used
for interpolation. If the number of input points is smaller than or
equal to the minimum number of points, global TPS interpolation is used.
If the number of input points is larger than the minimum number of
points, tiled local TPS interpolation is used. Tile sizes are variable
and dependent on the extents of the **min** nearest neighbors when a new
tile is generated.

The **smooth** option can be used to reduce the influence of the splines
and increase the influence of the covariables. Without covariables, the
resulting surface will be smoother. With covariables and a large
smooting value, the resulting surface will be mainly determined by the
multiple regression component.

The **overlap** option controls how much tiles are overlapping when the
**min** option is smaller than the numer of input points. Tiling
artefacts occur with low values for the **min** option and the
**overlap** option. Increasing both options will reduce tiling artefacts
but processing will take more time. Values for the **overlap** option
must be between 0 and 1.

The module works best with evenly spaced sparse points. In case of
highly unevenly spaced points, e.g. remote sensing data with gaps due to
cloud cover, the **thin** option should be used in order to avoid tiling
artefacts, otherwise a high number of minimum points and a large
**overlap** value are required, slowing down the module.

The **memory** option controls only how much memory should be used for
the covariables and the intermediate output. The input points are always
completely loaded to memory.

## EXAMPLES

The computational region setting for the following examples:

```sh
g.region -p rast=elev_state_500m
```

### Basic interpolation

Interpolation of 30 year precipitation normals in the North Carlolina
sample dataset:

```sh
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140
```

### Interpolation with a covariable

```sh
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140 covars=elev_state_500m
```

### Interpolation with a covariable and smoothing

```sh
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=140 covars=elev_state_500m smooth=0.1
```

### Tiled interpolation with a covariable and smoothing

```sh
v.surf.tps input=precip_30ynormals_3d output=precip_30ynormals_3d \
           column=annual min=20 covars=elev_state_500m smooth=0.1 \
           overlap=0.1
```

![image-alt](v_surf_tps.png)

*Precipitation computed based on annual normals and elevation as a
covariable*

## REFERENCES

  - Hutchinson MF, 1995, Interpolating mean rainfall using thin plate
    smoothing splines. International Journal of Geographical Information
    Systems, 9(4), pp. 385-403
  - Wahba G, 1990, Spline models for observational data. In CBMS-NSF
    Regional Conference Series in Applied Mathematics. Philadelpia:
    Society for Industrial and Applied Mathematics

## SEE ALSO

*[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.rst.html),
[v.surf.rst](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html),
[v.surf.idw](https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html)*

## AUTHOR

Markus Metz
