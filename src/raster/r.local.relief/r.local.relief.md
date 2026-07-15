## DESCRIPTION

*r.local.relief* generates a local relief model (LRM) from lidar-derived
high-resolution DEMs. Local relief models enhance the visibility of
small-scale surface features by removing large-scale landforms from the
DEM.

Generating the LRM is accomplished in 7 steps (Hesse 2010:69):

1. Creation of the DEM from the LIDAR data. Buildings, trees and other
    objects on the earth's surface should be removed.
2. Apply a low pass filter to the DEM. The low pass filter approximates
    the large-scale landforms. The neighborhood size of the low pass
    filter determines the scale of features that will be visible in the
    LRM. A default neighborhood size of 11 is used.
3. Subtract the low-pass filter result from the DEM to get the local
    relief.
4. Extract the zero contour lines from the difference map.
5. Extract the input DEM's elevation values along the zero contour
    lines.
6. Create a purged DEM by interpolating the null values between the
    rasterized contours generated in the previous step. This layer
    represents the large-scale landforms that will be removed to expose
    the local relief in the final step.
7. Subtract the purged DEM from the original DEM to get the local
    relief model.

The interpolation step is performed by the
*[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html)*
module by default (using cubic interpolation). If this is not working on
your data, you can use *-v* flag to use
*[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*
cubic interpolation instead (this might be slower on some types of
data).

## OUTPUT

The final local relief model is named according to the *output*
parameter. When the *-i* flag is specified, *r.local.relief* creates
additional output files representing the intermediate steps in the LRM
generation process. The names and number of the intermediate files vary
depending on whether
*[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html)*
(default) or
*[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*
(specified by using the *-v* flag) is used for interpolation. The
intermediate maps are composed of the user-specified *output* parameter
and suffixes describing the intermediate map.

Without using the *-v* flag
(*[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html)*
interpolation), intermediate maps have the following suffixes:

- `_smooth_elevation`: The result of running the low pass filter on
    the DEM.
- `_subtracted_smooth_elevation`: The result of subtracting the low
    pass filter map from the DEM.
- `_raster_contours_with_values`: The rasterized zero contours with
    the values from elevation map.
- `_purged_elevation`: The raster interpolated from the
    \_raster\_contours\_with\_values map based that represents the
    large-scale landforms.

With using the *-v* flag
(*[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*
interpolation), intermediate maps have the following suffixes:

- `_smooth_elevation`: The result of running the low pass filter on
    the DEM.
- `_subtracted_smooth_elevation`: The result of subtracting the low
    pass filter map from the DEM.
- `_vector_contours`: The zero contours extracted from the DEM.
- `_contour_points`: The points extractacted along the zero contour
    lines with the input DEM elevation values.
- `_purged_elevation`: The raster interpolated from the
    \_contour\_points map that represents the large-scale landforms.

The module sets equalized gray scale color table for local relief model
map and for the elevation difference (subtracted elevations). The color
tables of other raster maps are set to the same color table as the input
elevation map has.

## EXAMPLE

Basic example using the default neighborhood size of 11:

```sh
r.local.relief input=elevation output=lrm11
```

Example with a custom neighborhood size of 25:

```sh
r.local.relief input=elevation output=lrm25 neighborhood_size=25
```

Example using the default neighborhood size of 11 and saving the
intermediate maps:

```sh
r.local.relief -i input=elevation output=lrm11
```

Example using the default neighborhood size of 11 with bspline
interpolation and saving the intermediate maps:

```sh
r.local.relief -i -v input=elevation output=lrm11
```

Example in NC sample location (area of Raleigh downtown):

```sh
# set the computational region to area of interest
g.region n=228010 s=223380 w=637980 e=644920 res=10

# compute local relief model
r.local.relief input=elevation output=elevation_lrm

# show the maps, e.g. using monitors
d.mon wx0
d.rast elevation
d.rast elevation_lrm

# try alternative red (negative values) and blue (positive values) color table
# color table shows only the high values which hides small streets
# for non-unix operating systems use file or interactive input in GUI
# instead of rules=- and EOF syntax
r.colors map=elevation_lrm@PERMANENT rules=- <<EOF
100% 0:0:255
0 255:255:255
0% 255:0:0
nv 255:255:255
default 255:255:255
EOF
```

![image-alt](r.local.relief.png)
![image-alt](r.local.relief_redblue.png)

Figure: Local relief model of downtown Raleigh area created from
elevation raster map in NC sample location with the default (gray scale)
color table and custom red (negative values) and blue (positive values)
color table

## SEE ALSO

*[r.relief](https://grass.osgeo.org/grass-stable/manuals/r.relief.html),
[r.shaded.pca](r.shaded.pca.md), [r.skyview](r.skyview.md)*

## REFERENCES

- Hesse, Ralf (2010). LiDAR-derived Local Relief Models - a new tool
    for archaeological prospection. *Archaeological Prospection*
    17:67-72.
- Bennett, Rebecca (2011). *Archaeological Remote Sensing:
    Visualization and Analysis of grass-dominated environments using
    laser scanning and digital spectra data.* Unpublished PhD Thesis.
    Electronic Document,
    <http://eprints.bournemouth.ac.uk/20459/1/Bennett%2C_Rebecca_PhD_Thesis_2011.pdf>,
    Accessed 25 February 2013. (provided bash script with
    *[v.surf.bspline](https://grass.osgeo.org/grass-stable/manuals/v.surf.bspline.html)*-based
    implementation)

## AUTHORS

Vaclav Petras, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/),  
Eric Goddard
