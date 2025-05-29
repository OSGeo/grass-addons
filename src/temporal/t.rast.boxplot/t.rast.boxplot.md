## DESCRIPTION

*t.rast.boxplot* draws boxplots of the raster in a space-time raster
data set (strds). The module can be used to display changes over time,
and how this varies within a area. It will plot all rasters in a strds.
To display a subset of a strds, the user first needs to create a new
strds with the required subset of raster layers. It will furthermore,
plot the boxplots using the *temporal granularity* of the strds.

The whiskers of the boxplots extend to the most extreme data point,
which is no more than **range** ✕ the interquartile range (iqr) from the
box. By default, a **range** of 1.5 is used, but the user can change
this. Note that range values need to be larger than 0.

There are a few plot format/layout options, including the option to
rotate the plot and the x-axis labels, print the boxplot(s) with
notches, and to include the outliers (by default, they are not
included). You can also set the limits of the y-axis (or the x-axis if
the -h flag is set). This makes it easier to compare the boxplots of two
time-series of, e.g., two different areas.

There are various options to format the boxplots, e.g., setting the
width and color of the boxplots, the color and thickness of the median
line(s), whisker line width, and flier marker type and color.

The default format of the date-time labels on the x-axis (or y-axis in
case the boxplots are plotted horizontally) depend on the temporal
granularity of the data. This can be changed by the user. For a list of
options, see the [Python strftime cheatsheet](https://strftime.org/).

Alternatively, the user can set the **d** flag. With this option, an
attempt is made to figure out the best tick locations and format to use,
and to make the format as compact as possible while still having
complete date information. Note, this will override the **data\_format**
setting. With this option, often not all boxplots will get a label.

By default, the resulting plot is displayed on screen. However, the user
can also save the plot to file using the **output** option. The format
is determined by the extension given by the user. So, if output =
outputfile.png, the plot will be saved as a PNG file. The user can set
the output size (in inches) and resolution (dpi) of the output image.

## NOTE

If you work with a large number of raster layers, or if the raster
layers are very large, try to avoid setting the **range** value very
low, as that may result in a massive number of outliers, slowing down
the computations and rendering of the plot.

The *t.rast.boxplot* module operates on the raster array defined by the
current region settings, not the original extent and resolution of the
input map. See
[g.region](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)
to understand the impact of the region settings on the calculations.

You can change the width of the boxplot using the **bx\_width**
parameter. The default value is 0.75, which means that the boxplot is
0.75 the maximum width between two consecutive periods. Importantly, the
function uses the time stamp unit (see
[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html))
to determine the maximum width. This means that if the time stamp unit
is in days, but the raster layers represent e.g., 10-day periods, you
need to multiply the **bx\_width** value you would normally use by 10 to
get the same relative width. See [this
post](https://ecodiv.earth/post/drawing-boxplots-of-raster-values/) for
an example.

## EXAMPLE

The first two examples use the MODIS Land Surface Temperature mapset.
First download the North Carolina sample data set from [this
link](https://grass.osgeo.org/download/data/#NorthCarolinaDataset).
Unzip the sample GRASS GIS dataset to a convenient location on your
computer. Next, download the [MODIS LST
mapset](https://grass.osgeo.org/sampledata/north_carolina/nc_spm_mapset_modis2015_2016_lst_grass8.zip)
and unzip it within the NC project. Now, open the mapset in GRASS GIS.

### Example 1

Plot the time series, using the default settings, except that we set the
dimension of the plot to 12 inch (ca. 30 cm) wide and 8 inch (ca. 20 cm)
height, and a dpi of 200

```sh
g.region raster=landclass96
t.rast.boxplot input=LST_Day_monthly@modis_lst \
plot_dimensions=12,8 dpi=200
```

![image-alt](t_rast_boxplot_01.png)

### Example 2

We use the same example as above, but this time, we change the color of
the boxplots and median lines to respectively green
(**bx\_color=green**) and white (**median\_color=white**), use the
default plot dimensions, set the font size to 8, and include the
outliers (**o** flag). Note that by plotting the outliers will increase
the time required to create the plot considerably.

For the outliers (fliers) we use orange squares (**flier\_marker=s** &
**flier\_color=orange**). We furthermore plot the boxplots horizontally
(**h** flag) and add grid lines (**g** flag). Note that for horizontal
plots, the labels are plotted horizontally (equal to
**rotate\_labels=0**) by default.

```sh
t.rast.boxplot -o -h -g  input=LST_Day_monthly@modis_lst \
bx_color=green median_color=white median_lw=0.8 bx_lw=0.8 \
flier_color=orange flier_size=1 flier_marker=s font_size=8
```

See [https://matplotlib.org/stable/tutorials/colors/colors.html](https://matplotlib.org/stable/tutorials/colors/colors.html)
for the different formats in which colors can be specified.

![image-alt](t_rast_boxplot_02.png)

### Example 3

In the following example, the date labels are changed, showing the
abbreviated name of the month, followed by the year (**date\_format="%B
%Y"**). The boxplot colors are set to white, and for the median line we
set the color to orange and the line width to 2. Lastly, the labels are
rotated 90℃ (the default for vertical plots is **rotate\_labels=45**).

```sh
t.rast.boxplot input=LST_Day_monthly@modis_lst rotate_labels=90 \
date_format="%B %Y" bx_color=white median_lw=2 median_color=red \
font_size=9
```

![image-alt](t_rast_boxplot_03.png)

### Example 4

If we want to plot 3-monthly patterns instead, we first need to create a
new strds. In the example below, the function *t.rast.aggregate* is used
to aggregate the LST\_Day\_monthly to a 3 month granularity.

```sh
t.rast.aggregate input=LST_Day_monthly@modis_lst output=LST_Day_3monthly \
basename=LST_3monthly granularity="3 months" method=average
```

Now, we can plot the 3-monthly temporal pattern using the newly created
strds as input.

```sh
t.rast.boxplot input=LST_Day_3monthly@modis_lst
```

As you can see below, the plot plots the boxplots using the 3-month
granularity of the input strds.

![image-alt](t_rast_boxplot_04.png)

## Acknowledgements

This work was carried in the framework of the [Save the tiger, save the
grassland, save the water](https://savethetiger.nl/) project by the
[Innovative Bio-Monitoring research
group](https://www.has.nl/en/has-research/research-groups/innovative-bio-monitoring-research-group)
of the HAS University of Applied Sciences.

## SEE ALSO

*[r.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.boxplot.html),
[r.series.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.series.boxplot.html),
[d.vect.colbp](https://grass.osgeo.org/grass-stable/manuals/addons/d.vect.colbp.html),
[r.scatterplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.scatterplot.html),
[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html),
[t.rast.aggregate](https://grass.osgeo.org/grass-stable/manuals/t.rast.aggregate.html)*

## AUTHOR

Paulo van Breugel  
Applied Geo-information Sciences  
[HAS University of Applied Sciences](https://www.hasuniversity.nl/)
