## DESCRIPTION

Module *r.skyview* computes skyview factor, a relief visualization
technique (Zaksek et al. 2011). The value of each cell is given by the
portion of visible sky (from that cell) limited by the surrounding
relief. The values range from 0 to 1. The lighter the value is, the more
open the terrain is.

When flag **-o** is set, r.skyview computes openness instead of skyview
factor. Openness (based on positive openness by Yokoyama et al. 2002)
takes into account zenith angles greater than 90 degrees, while skyview
limits zenith angles to 90 degrees (celestial hemisphere). This makes
difference for example for visualization of horizontal planes and
slopes. Openness values range from 0 to 2.

## NOTES

Module
*[r.horizon](https://grass.osgeo.org/grass-stable/manuals/r.horizon.html)*
is used to compute elevation angles.

## EXAMPLES

We compute the skyview factor map of the North Carolina sample dataset
`elevation` map:

```sh
g.region raster=elevation
r.skyview input=elevation output=elevation_skyview ndir=8
```

![image-alt](elevation.jpg)

## SEE ALSO

*[r.horizon](https://grass.osgeo.org/grass-stable/manuals/r.horizon.html),
[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html),
[r.shaded.pca](r.shaded.pca.md), [r.local.relief](r.local.relief.md)*

## REFERENCES

- Zaksek K, Ostir K, Kokalj Z. *Sky-View Factor as a Relief
    Visualization Technique.* Remote Sensing. 2011; 3(2):398-415.
- Yokoyama R, Shirasawa M, Pike J R. *Visualizing topography by
    Openness: A new application of image processing to digital elevation
    models.* Photogrammetric engineering and remote sensing 68.3 (2002):
    257-266.

## AUTHOR

Anna Petrasova, [NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)
