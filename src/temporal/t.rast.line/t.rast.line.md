## DESCRIPTION

*t.rast.line* draws trend lines of the average values of the input
raster layers in a space-time raster dataset (strds). The trend line
represents the average values of the current computational region. The
user can optionally show an error bar for each trend line using the
**error** option. The error bar can be based on the standard deviation
(SD) or standard error (SE). The user can multiply the SD or SE to
increase or decrease the width of the error band using the **n** option.

If a zonal raster map is provided, using the **zones** option, trend
lines are plotted for each zone (category) in the zonal raster layer.
The zonal raster should be a single, static integer raster map.

[![image-alt](t_rast_line_07.png)](t_rast_line_07.png)  
*Trend lines (average ± SD) for three land cover categories of the
FCover for the fraction of green vegetation cover for the period
2014-2019.*

The function will plot all rasters in the strds. Alternatively, the user
can select a subset of the raster layers using the WHERE conditions.

By default, the resulting plot is displayed on a new screen. However,
the user can also save the plot to a file using the **output** option.
The format is determined by the extension given by the user. So, if
output = outputfile.png, the plot will be saved as a \*png\* file. The
user can set the output size (in inches) and resolution (dpi).

There are a few plot format and layout options, including the option to
plot grid lines and the legend, rotate the labels, change the font size
of the labels, and change the date format.

If a zonal map is provided, the lines will take the colors of the
categories on that map. If the zonal map does not have a color table,
the lines will be assigned random colors.

The default format of the date-time labels on the x-axis depend on the
temporal granularity of the data. This can be changed by the user using
the **date\_format** option. For a list of options, see the [Python
strftime cheatsheet](https://strftime.org/).

The **where** options allows allows performing different selections of
maps registered in the space-time datasets. For example, with
*start\_time \< '2020-01-01'* the time series is limited to all maps
with a start time before the given date. For more details, see [this
page](https://grass.osgeo.org/grass83/manuals/temporalintro.html#modules-to-process-space-time-raster-datasets)
for more details.

## NOTE

The user can specify the number of threads to be used with the
**nprocs** parameter. However, note that parallelization does not work
when the MASK is set. If speed is an issue, it is recommended to create
a new zonal layer using, e.g., *r.mapcalc*, remove the MASK and use the
newly created zonal layer.

The t.rast.line module operates on the raster array defined by the
current region settings, not the original extent and resolution of the
input map. See
[g.region](https://grass.osgeo.org/grass-stable/manuals/r.univar.html)
to understand the impact of the region settings on the calculations.

## EXAMPLE

The next two examples use the North Carolina full (NC) and North
Carolina Climate 2000-2012 data sets, which can be downloaded from
([this download
page](https://grass.osgeo.org/download/data/#NorthCarolinaDataset)).

First step is to create temporal datasets *tempmean* and *precip\_sum*
for the rainfall and temperature time series respectively, as described
in [this
tutorial](https://ncsu-geoforall-lab.github.io/grass-temporal-workshop).
These will serve as input for the examples below. The *landclass\_96*
raster layer in the PERMANENT mapset of the NC project (location) will
be used as zonal map.

### Example 1

Plot the tempmean time series. Note that you can speed up the process
considerably by making use of the cores and threads of your computer.
You can set the number of threads to be used with the **nprocs** option.

```sh
g.region raster=2000_01_tempmean
t.rast.line input=tempmean nprocs=10
```

![image-alt](t_rast_line_01.png)

### Example 2

Plot the rainfall time series. Set the color of the line to green, and
choose the option to plot an error band based on the *standard
deviation* using the **error** option.

```sh
t.rast.line input=precip_sum error=sd line_color=0:128:0:255 nprocs=10
```

![image-alt](t_rast_line_02.png)

### Example 3

Now, compare the temporal rainfall patterns in the inland Avery County
and Brunswick County on the coast. Set the flag **-l** to include a
legend.

```sh
# Create a zonal map
echo "11 = 1 Avery
19 = 2 Brunswick
* = NULL" > recl.txt

r.reclass input=boundary_county_500m output=comparison_counties rules=recl.txt

t.rast.line -l input=tempmean zones=comparison_counties error=sd nprocs=10
```

![image-alt](t_rast_line_03.png)

Because the zonal map does not have a color table, the lines have a
random color.

### Example 4

If you want the colors of the trend lines to match the color of the
zonal categories, make sure to define the category colors.

```sh
# Define colors
echo "1 purple
2 green"> color_rules.txt
r.colors map=comparison_counties rules=color_rules.txt

# Create the plot

t.rast.line -l -g input=tempmean zones=comparison_counties error=sd nprocs=10
```

Whether this was the right color choice is debatable, but, the colors of
the graph match those of the zones of the map. Note that with the **g**
flag, vertical grid lines are drawn.

![image-alt](t_rast_line_04c.png)

### Example 5

You can zoom in on a specific period using the **where** option. For
example, to plot the trend line for the time period 01-01-2004 to
01-01-2010, you can use the following:

```sh
t.rast.line -l -g input=tempmean zones=comparison_counties error=sd nprocs=10 \
    where="start_time > '2004-01-01  00:00:00' AND start_time < '2010-01-01'"
```

When using greater than (\>), the date alone is not enough, also also
the time needs to be set explicitly. This is not needed when using
smaller than (\<).

![image-alt](t_rast_line_05.png)

### Example 6

If you want to create and compare two plots, it might be useful to force
both to use a specific scale by using the **y\_axis\_limits** parameter
and the same y-axis label by using the **y\_label** parameter.

```sh
t.rast.line -l -g input=tempmean \
    zones=comparison_counties error=sd nprocs=10 \
    y_axis_limits=-10,40 y_label="mean temperature"
```

![image-alt](t_rast_line_06.png)

## Acknowledgements

This work was carried out within the framework of the [Save the Tiger,
Save the Grassland, Save the Water](https://savethetiger.nl/) project by
the [Innovative Bio-Monitoring research
group](https://www.has.nl/en/has-research/research-groups/innovative-bio-monitoring-research-group)
of the HAS University of Applied Sciences.

## SEE ALSO

*[r.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/t.rast.boxplot.html),
[r.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.boxplot.html),
[r.series.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.series.boxplot.html),
[d.vect.colbp](https://grass.osgeo.org/grass-stable/manuals/addons/d.vect.colbp.html),
[r.scatterplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.scatterplot.html),
[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html),*

## AUTHOR

Paulo van Breugel  
Applied Geo-information Sciences  
[HAS green academy, University of Applied
Sciences](https://www.has.nl/)
