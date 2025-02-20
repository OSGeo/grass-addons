## DESCRIPTION

*v.centerpoint* calculates center points for point clouds, lines and
areas. Center points can be centers of gravity (coordinates' mean) or
geometric medians (points of minimum distance, which is more robust in
case of outliers.

For points, center points are calculated considering all points. For
lines and areas, center points are calculated for each line or area
separately.

If no output vector is given, center points are printed to stdout in
ASCII point format:

```sh
<easting>|<northing>|<height>|<cat>
```

The category values are

  - **1** - mean of points
  - **2** - median of points
  - **3** - point closest to median of points
  - **4** - mid point of each line
  - **5** - mean of each line
  - **6** - median of each line
  - **7** - mean of each area
  - **8** - median of each area using area triangulation
  - **9** - median of each area using boundaries

If an output vector is given, categories of the respective lines and
areas are transferred from the selected layer to layer 1. Layer 2 holds
the same category values as for output to stdout.

#### Point centers

  - **mean** - center of gravity, mean of all point coordinates
  - **median** - geometric median, minimum distance to all points
  - **pmedian** - point closest to the geometric median

#### Line centers

  - **mid** - the mid point of each line, lies exactly on the line
  - **mean** - center of gravity, mean of all line segments, might not
    lie on the line
  - **median** - geometric median, minimum distance to all line
    segments, might not lie on the line

#### Area centers

  - **mean** - center of gravity, calculated using area triangulation
  - **median** - geometric median, minimum distance to area
    triangulation, might not lie inside the area
  - **bmedian** - geometric median, minimum distance to boundary
    segments, might not lie inside the area

## EXAMPLE

Calculate center of gravity for the LiDAR point cloud 'elev\_lid\_bepts'
in the North Carolina sample dataset:

```sh
v.centerpoint input=elev_lid_bepts output=elev_lid_bepts_mean
```

```sh
v.centerpoint in=urbanarea out=urbanarea_median acenter=median
```

## SEE ALSO

*[v.centroids](https://grass.osgeo.org/grass-stable/manuals/v.centroids.html)*

## AUTHOR

Markus Metz
