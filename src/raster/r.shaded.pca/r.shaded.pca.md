## DESCRIPTION

*r.shaded.pca* is a tool for the generation of RGB composite of the
three main components of PCA created from different hill shades (created
by
*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html)*).

### Input parameters explanation

Input parameters are the same as for
*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html)*
module except for an *azimuth* parameter which is replaced by
*nazimuths* parameter (we need to specify number of different azimuths
rather than one) and for an *nprocs* parameter which adds the
possibility to run the shades creation
(*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html)*)
in parallel. However, the speed of
*[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html)*
limits the overall speed of this module. In order to provide simple
interface, it is not possible to customize principal component analyses
which uses the default settings of the
*[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html)*
module.

### Output parameters explanation

The the standard output map is an RGB composition of first three
principal components where components are assigned to red, green and
blue colors in this order. If you want to create your own RGB
composition, HIS composition or do another analyses you can specify the
*pca\_shades\_basename* parameter. If this parameter is specified, the
module outputs the PCA maps as created during the process by
*[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html)*.
Moreover, if you would like to add one of the shades to your
composition, you can specify the *shades\_basename* parameter then the
module will output also the hill shade maps as created during the
process by
*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html)*.
One of the shades can be used to subtract the intensity channel in HIS
composition or just as an overlay in your visualization tool.

## EXAMPLE

```sh
# basic example with changed vertical exaggeration
r.shaded.pca input=elevation output=elevation_pca_shaded zscale=100

# example of more complicated settings
# including output shades and principal component maps
r.shaded.pca input=elevation output=elevation_pca_shaded \
 zscale=100 altitude=15  nazimuths=16 nprocs=4 \
 shades_basename=elevation_pca_shaded_shades pca_shades_basename=elevation_pca_shaded_pcs
```

![image-alt](r.shaded.pca.png)

Figure: The RGB composition of first 3 PCA components (output from
*r.shaded.pca* with default values)

## SEE ALSO

*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html),
[i.pca](https://grass.osgeo.org/grass-stable/manuals/i.pca.html),
[r.local.relief](r.local.relief.md), [r.skyview](r.skyview.md)*

## REFERENCES

Devereux, B. J., Amable, G. S., & Crow, P. P. (2008). Visualisation of
LiDAR terrain models for archaeological feature detection. Antiquity,
82(316), 470-479.

## AUTHOR

Vaclav Petras, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/)
