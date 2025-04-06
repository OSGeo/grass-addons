## DESCRIPTION

*v.scatterplot* draws a scatterplot of the value in one column against
the values in another column. There are a few layout options, including
the option to set the color of the dots, the color, line type, and width
of the trend line, and the font size of the axis and tic labels.

Instead of a fixed color, dots can be colored using colors from a
user-defined column, or by the spatial density of nearby points, using
the option `type=density`. The spatial density is computed by grouping
the points in 2D bins. The number of bins along the x-axis and y-axis is
user-defined. The user can select a color map from a list of sequential
colormaps and perceptually uniform sequential colormaps. See the
matplotlib [manual
page](https://matplotlib.org/stable/users/explain/colors/colormaps.html)
for details. Use the **-r** flag to reverse the order of the colors.

By default, the resulting plot is displayed on screen (default).
However, the user can also save the plot to a file using the
**file\_name** option. The format is determined by the extension given
by the user. So, if `file_name = outputfile.png`, the plot will be saved
as a PNG file.

A linear or polynomial trend line with user-defined degrees can be drawn
on top of the scatter/density plot. If this option is enables, the R2
and trend line equation are printed to the commmand line.

A confidence ellipse of the covariance of the two variables can be
plotted on top of the scatterplot, following the method described
[here](https://carstenschelp.github.io/2018/09/14/Plot_Confidence_Ellipse_001.html),
and using the code described
[here](https://matplotlib.org/stable/gallery/statistics/confidence_ellipse.html).
The radius of the ellipse can be controlled by **n** which is the number
of standard deviations (SD). The default is 2 SD, which results in an
ellipse that encloses around 95% of the points. Optionally, separate
confidence ellipses can be drawn for groups defined in the column
**groups**. Groups can be assigned a random color, or a color based on
the RGB colors in a user-defined column. Note, all records in the group
should have the same color.

The user has the option to limit/expand the X-axis (**x\_axis\_limits**)
and Y-axis (**y\_axis\_limits**). This can e.g., make it easier to
compare different plots.

## EXAMPLES

### Example 1

For the examples below, the NCA sample data set from [GRASS GIS
website](https://grass.osgeo.org/download/data/) will be used

Create a new mapset and Use the layer *lsat7\_2002\_10@PERMANENT* to set
the region.

```sh
g.mapset -c mapset=scatterplot
g.region raster=lsat7_2002_10@PERMANENT
```

Get the list of Landsat layers from the Permanent mapset. Use this as
input for *i.pca* to create principal component layers.

```sh
lcc=`g.list type="raster" mapset="PERMANENT" pattern="lsat7_*" sep=,`
i.pca -n input=$lcc output=pca rescale=0,100
```

Create 5000 random points, retrieve the raster value from the first two
PCA layers for each point location of the random points, and write these
values to the columns *pca\_1* and *pca\_2* in the attribute table of
*randompoints*.

```sh
r.random input=elevation npoints=5000 vector=randompoints seed=10
v.what.rast map=randompoints raster=pca.1 column=pca_1
v.what.rast map=randompoints raster=pca.2 column=pca_2
```

Create a scatterplot, plotting the values from the column *pca\_1* on
the X-axis and *pca\_2* on the Y-asix, with blue dots.

```sh
v.scatterplot map=randompoints x=pca_1 y=pca_2 color=blue
```

[![image-alt](v_scatterplot_01.png)](v_scatterplot_01.png)  
*Figure 1. Scatterplot of pca\_1 against pca\_2.*

### Example 2

Create a density scatter of the values from *pca\_1* and *pca\_2*. Add a
red dashed polynomial trend line with degree 2.

```sh
v.scatterplot map=randompoints x=pca_1 y=pca_2 trendline=polynomial \
              degree=2 line_color=red type=density bins=10,10
```

[![image-alt](v_scatterplot_02.png)](v_scatterplot_02.png)  
*Figure 2. Density scatterplot of pca\_1 against pca\_2. The dashed red
line gives the polynomial trend line (R²=0.149)*

### Example 3

Retrieves raster value from the raster layer *landclass96*, and write
these values to the column *landuse* in the attribute table of
*randompoints*. Next, transfer the raster colors of the raster layer
*landclass96* to the new column *RGB* of the attribute table of
*randompoints*.

```sh
v.what.rast map=randompoints raster=landclass96 column=landuse
v.colors map=randompoints use=attr column=landuse \
         raster=landclass96@PERMANENT rgb_column=RGB
```

Create a scatterplot, using the colors from the RGB column. Set the size
of the dots to 8.

```sh
v.scatterplot map=randompoints x=pca_1 y=pca_2 s=8 rgbcolumn=RGB
```

[![image-alt](v_scatterplot_03.png)](v_scatterplot_03.png)  
*Figure 3. Scatterplot of pca\_1 against pca\_1. Colors represent the
land use categories in the point locations based on the landclass96
map.*

### Example 4

Rename the PCA layers to remove the dots from the name. Next, use the
[v.what.rast.label](https://grass.osgeo.org/grass-stable/manuals/addons/v.what.rast.label.html)
addon to sample the values of the raster layers *pca.1* and *pca.2*, and
the values + labels of the *landclass96*. Add a column with the
landclass colors using *v.colors*.

```sh
g.rename raster=pca.1,pca_1
g.rename raster=pca.2,pca_2
v.what.rast.label vector=randompoints raster=landclass96 \
         raster2=pca_1,pca_2 output=randompoints2
v.colors map=randompoints2 use=attr column=landclass96_ID \
         raster=landclass96 rgb_column=RGB
```

Extract the points with the categories forest (5), water (6) and
developed (1). Create a scatterplot of pca\_1 against pca\_2 and add the
2 SD confidence ellipse of the covariance of the two variables for each
of the land use categories, coloring both the dots and ellipses using
the landclass colors.

```sh
v.extract input=randompoints2 \
          where='landclass96_ID=1 OR landclass96_ID=5 OR landclass96_ID=6' \
          output=forwatdev
v.scatterplot -e map=forwatdev x=pca_1 y=pca_2 rgbcolumn=RGB s=5  \
              groups=landclass96 groups_rgb=RGB
```

[![image-alt](v_scatterplot_04.png)](v_scatterplot_04.png)  
*Figure 4. Scatterplot with confidence ellipses per land class. The
radius of the ellipses is 2 SD.*

## SEE ALSO

*[d.vect.colbp](https://grass.osgeo.org/grass-stable/manuals/addons/d.vect.colbp.html),
[d.vect.colhist](https://grass.osgeo.org/grass-stable/manuals/addons/d.vect.colhist.html),
[r.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.boxplot.html),
[r.series.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.series.boxplot.html),
[t.rast.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/t.rast.boxplot.html),
[r.scatterplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.scatterplot.html)
[r3.scatterplot](https://grass.osgeo.org/grass-stable/manuals/addons/r3.scatterplot.html)*

## AUTHOR

Paulo van Breugel Applied Geo-information Sciences HAS green academy,
University of Applied Sciences
