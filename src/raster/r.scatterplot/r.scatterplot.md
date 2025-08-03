## DESCRIPTION

The *r.scatterplot* module takes raster maps and creates a scatter plot
which is a vector map and where individual points in the scatter plot
are vector points. As with any scatter plot the X coordinates of the
points represent values from the first raster map and the Y coordinates
represent values from the second raster map. Consequently, the vector
map is placed in the combined value space of the original raster maps
and its geographic position should be ignored. Typically, it is
necessary to zoom or to change computational in order to view the
scatter plot or to perform further computations on the result.

With the default settings, the *r.scatterplot* output allows measuring
and querying of the values in the scatter plot. Settings such as
**xscale** or **position** option change the coordinates and make some
of the measurements wrong.

### Multiple variables

If more than two raster maps are provided to the **input** option,
*r.scatterplot* creates a scatter plot for each unique pair of input
maps. For example, if A, B, C, and D are the inputs, *r.scatterplot*
creates scatter plots for A and B, A and C, A and D, B and C, B and D,
and finally C and D. Each pair is part of different vector map layer.
*r.scatterplot* provides textual output which specifies the pairs and
associated layers.

A 3D scatter plot can be generated when the **z\_raster** option is
provided. A third variable is added to each scatter plot and each point
has Z coordinate which represents this third variable.

Each point can also have a color based on an additional variable based
on the values from **color\_raster**. Values from a raster are stored as
categories, i.e. floating point values are truncated to integers, and a
color table based on the input raster color table is assigned to the
vector map.

The **z\_raster** and **color\_raster** can be the same. This can help
with understanding the 3D scatter plot and makes the third variable
visible in 2D as well. When **z\_raster** and **color\_raster** are the
same, total of four variables are associated with one point.

![image-alt](r_scatterplot_2_variables.png)
![image-alt](r_scatterplot_2_variables_3rd_color.png)
![image-alt](r_scatterplot_2_variables_3rd_z.png)

*Figure: One scatter plot of two variables (left), the same scatter plot
but with color showing third variable (middle), again the same scatter
plot in 3D where Z represents a third variable (right).*

![image-alt](r_scatterplot_2_variables_3rd_z_4th_color.png)
![image-alt](r_scatterplot_2_variables_3rd_z_4th_color2.png)

*Figure: One scatter plot in with one variable as Z coordinate and
another variable as color (two rotated views).*

### Layout

When working only with variable, X axis represents the first one and Y
axis the second one. With more than one variable, the individual scatter
plots for individual pairs of variables are at the same place. In this
case, the coordinates show the actual values of the variables. Each
scatter plot is placed into a separate layer of the output vector map.

![image-alt](r_scatterplot_3_variables_3_colors_overlap.png)

*Figure: Three overlapping scatter plots of three variables A, B, and C.
Individual scatter plots are distinguished by color. The colors can be
obtained using `d.vect layer=-1 -c`.*

If visualization is more important than preserving the actual values,
the **-s** flag can be used. This will place the scatter plots next to
each other separated by values provided using **spacing** option.

The layout options can be still combined with additional variables
represented as Z coordinate or color. In that case, Z coordinate or
color is same for all the scatter plots.

![image-alt](r_scatterplot_3_variables_3_colors.png)

*Figure: Three scatter plots of three variables A, B, and C. First one
is A and B, second A and C, and third B and C.*

![image-alt](r_scatterplot_3_variables.png)

*Figure: Three scatter plots of three variables A, B, and C with color
showing a fourth variable D in all scatter plots.*

The options **xscale**, **yscale** and **zscale** will cause the values
to be rescaled before they are stored as point coordinates. This is
useful for visualization when one of the variables has significantly
different range than the other or when the scatter plot is shown with
other data and must fit a certain area. The **position** option is used
to place the scatter plot to any given coordinates. Similarly, **-w**
flag can be used to place it to the south-west corner of the computation
region.

## NOTES

The resulting vector will have as many points as there is 3D raster
cells in the current computational region. It might be appropriate to
use coarser resolution for the scatter plot than for the other
computations. However, note that the some values will be skipped which
may lead, e.g. to missing some outliers.

The **color\_raster** input is expected to be categorical raster or have
values which won't loose anything when converted from floating point to
integer. This is because vector categories are used to store the
**color\_raster** values and carry association with the color.

The visualization of the output vector map has potentially the same
issue as visualization of any vector with many points. The points cover
each other and above certain density of points, it is not possible to
compare relative density in the scatter plot. Furthermore, if colors are
associated with the points, the colors of points rendered last are those
which are visible, not actually showing the prevailing color (value).
The modules
*[v.mkgrid](https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html)*
and
*[v.vect.stats](https://grass.osgeo.org/grass-stable/manuals/v.vect.stats.html)*
can be used to overcome this issue.

## EXAMPLES

### Landsat bands

In the full North Carolina sample location, set the computation region
to one of the raster maps:

```sh
g.region raster=lsat7_2002_30
```

Create the scatter plot:

```sh
r.scatterplot input=lsat7_2002_30,lsat7_2002_40 output=scatterplot color_raster=landclass96
```

![image-alt](r_scatterplot.png)

*Figure: Scatter plot showing red and near infrared Landsat bands
colored using land cover classes*

### High density scatter plots

In an ideal case, the scatter plot is computed with the computation
region resolution set to the resolutions of one of the rasters (which
ideally matches the other raster as well):

```sh
g.region raster=lsat7_2002_30 -p
r.scatterplot input=lsat7_2002_30,lsat7_2002_40 output=scatterplot_full_res
```

This best describes the actual state of the data, but unfortunately this
creates a lot of points which must be processed and rendered. Therefore,
it is also possible to compute the scatter plot in a lower resolution by
changing the computational region resolution:

```sh
g.region raster=lsat7_2002_30 res=120 -p
r.scatterplot input=lsat7_2002_30,lsat7_2002_40 output=scatterplot_res_120
```

Reducing the resolution creates a possibility of missing some outliers
or even smaller groups as some of the cells are just ignored, but
typically the general shape of the scatter plot is preserved. In any
case, with less points, every operation will by much faster.

![image-alt](r_scatterplot_density_full.png)
![image-alt](r_scatterplot_density_res_120.png)
![image-alt](r_scatterplot_density_res_240.png)

*Figure: Scatter plots computed with different computational region
resolutions; first one is with full raster resolution (\~30 m) second
with resolution 120 m, and third with 240 m*

Another way of dealing with hight density scatter plots is to bin the
points into cells of a rectangular grid. Number of points per cells with
influence color of the cell, so the density will be expressed clearly.
The scatter plot can be computed in full resolution:

```sh
g.region raster=lsat7_2002_30 -p
r.scatterplot input=lsat7_2002_30,lsat7_2002_40 output=scatterplot
```

To create the grid the computation region extent should match the
scatter plot extent. The resolution determines the size of the grid
cells. 5 is a good size for data from 0 to 255.

```sh
g.region vector=scatterplot res=5 -p
```

The grid can be created using
*[v.mkgrid](https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html)*
module, the binning done using
*[v.vect.stats](https://grass.osgeo.org/grass-stable/manuals/v.vect.stats.html)*,
and finally the color is set using
*[v.colors](https://grass.osgeo.org/grass-stable/manuals/v.colors.html)*.

```sh
v.mkgrid map=scatterplot_grid
v.vect.stats points=scatterplot areas=scatterplot_grid count_column=count
v.colors map=scatterplot_grid use=attr column=count color=viridis
```

The *[d.vect](https://grass.osgeo.org/grass-stable/manuals/d.vect.html)*
module picks up the color table automatically, but it is advantageous to
also specify that only the grid cells with non-zero count of points
should be displayed using `where="count > 0"`:

```sh
d.vect map=scatterplot_grid where="count > 0" icon=basic/point
```

To get more interesting and sometimes smoother look, hexagonal grid can
be used:

```sh
v.mkgrid -h map=scatterplot_grid
```

Alternatively, a smaller cell size can be used. When the cell size is
the same as the distance between the points, like for example using
cells size 1 with integer rasters, the grid needs to be shifted so that
the points fall into the middle of the cells rather than on the edges or
corners. For these purposes the
*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*
accepts modifications of the current extent values:

```sh
g.region vector=scatterplot res=1 w=w-0.5 e=e+0.5 s=s-0.5 n=n+0.5
```

![image-alt](r_scatterplot_density_grid_rectangles.png)
![image-alt](r_scatterplot_density_grid_hexagons.png)
![image-alt](r_scatterplot_density_grid_rectangles_res_1.png)

*Figure: High density scatter plot visualized using binning into
rectangular grid, hexagonal grid, and dense rectangular grid*

## SEE ALSO

*[r.stats](https://grass.osgeo.org/grass-stable/manuals/r.stats.html),
[d.correlate](https://grass.osgeo.org/grass-stable/manuals/d.correlate.html),
[r3.scatterplot](r3.scatterplot.md),
[v.mkgrid](https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html),
[v.vect.stats](https://grass.osgeo.org/grass-stable/manuals/v.vect.stats.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*

## AUTHOR

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
