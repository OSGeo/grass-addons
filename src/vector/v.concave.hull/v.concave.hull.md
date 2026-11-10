## DESCRIPTION

*v.concave.hull* creates a concave hull around points. Contrary to a
convex hull, a concave hull can describe the shape of a point cloud.

## EXAMPLES

### Creating a convex and a concave hull

Creating a convex and a concave hull around schools\_wake in the North
Carolina sample dataset:

```sh
v.hull in=schools_wake out=schools_wake_convex
v.concave.hull in=schools_wake out=schools_wake_concave
```

Convex hull around schools:

![image-alt](v_concave_convex.png)

Concave hull around schools:

![image-alt](v_concave_concave.png)

### Creating Alpha shapes

Alpha shapes around points (left: threshold=8; right: threshold=0.5):

![image-alt](v_concave_alpha_8.png)  
![image-alt](v_concave_alpha_0_5.png)

## SEE ALSO

*[v.hull](https://grass.osgeo.org/grass-stable/manuals/v.hull.html),
[v.buffer,](https://grass.osgeo.org/grass-stable/manuals/v.buffer.html),
[v.kernel](https://grass.osgeo.org/grass-stable/manuals/v.kernel.html)*

## AUTHOR

Markus Metz
