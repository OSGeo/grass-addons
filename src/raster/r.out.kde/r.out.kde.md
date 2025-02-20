## DESCRIPTION

*r.out.kde* creates an image file (e.g., PNG, JPG, or GIF) where the
**input** raster is rendered on top of **background** raster with
varying transparency based on the values of the **input** raster. This
can be used for example for visualization of kernel density estimate
(KDE).

With logistic **method**, values are scaled so that lower values are
more transparent and higher values are more opaque than with linear
scaling.

This module requires [Python Imaging
Library](https://pillow.readthedocs.io/en/stable/) (already required for
GRASS GIS).

## EXAMPLE

In this example, we visualize KDE of schools on top of shaded relief
map.

```sh
g.region raster=elevation
# create background map
r.relief input=elevation output=relief
# compute kernel density estimate
v.kernel input=schools_wake output=schools_density radius=4000 multiplier=1000000
r.colors map=schools_density color=bcyr
r.out.kde input=schools_density background=relief method=logistic output=output.png
```

![image-alt](r_out_kde.png)  

## SEE ALSO

*[d.rast](https://grass.osgeo.org/grass-stable/manuals/d.rast.html),
[v.kernel](https://grass.osgeo.org/grass-stable/manuals/v.kernel.html)*  
  
[Logistic function](https://en.wikipedia.org/wiki/Logistic_function)

## AUTHOR

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
