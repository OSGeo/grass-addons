## DESCRIPTION

*r.centroids* is a wrapper function for
[r.volume](https://grass.osgeo.org/grass-stable/manuals/r.volume.html)
that computes the center point of raster clumps of data (neighboring,
same-valued pixels). The centroids will always fall within the clump so
they may not be the true, mathematical centroid. The centroids will
always fall at the center of a pixel.

*r.centroids* requires an input raster containing clumps of data such as
the output of
[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html).

## EXAMPLES

Find the centroids of the basins map (North Carolina sample dataset).
First, set computational area.

```sh
g.region raster=basin_50K
```

Then, compute the centroids.

```sh
r.centroids input=basin_50K output=centroids50K
```

[![image-alt](r_centroids_basin_50K.png)](r_centroids_basin_50K.png)

## SEE ALSO

*[r.volume](https://grass.osgeo.org/grass-stable/manuals/r.volume.html)*
*[r.clump](https://grass.osgeo.org/grass-stable/manuals/r.clump.html)*

## AUTHOR

Caitlin Haedrich, *Center for Geospatial Analytics, North Carolina State
University*, January, 2021.
