## DESCRIPTION

*r.seriesboxplot* draws boxplots of series of input raster layers. It
can be used to display both temporal patterns and spatial variation.

The whiskers of the boxplots extend to the most extreme data point,
which is no more than **range** ✕ the interquartile range (iqr) from the
box. By default, a **range** of 1.5 is used, but the user can change
this. Note that range values need to be larger than 0. By default,
outliers are not included in the plot. Set the -o flag to include them
in the plot.

There are a few layout options, including the option to rotate the plot
and the x-axis labels, print the boxplot(s) with notches, and define the
color of the boxplots.

By default, the raster names are used as labels, but the user can
explicitly define the labels (example 3 below). The number of labels
need to be the same as the number of input raster layers.

By default, the resulting plot is displayed on screen. However, the user
can also save the plot to file using the **output** option. The format
is determined by the extension given by the user. So, if **output =
outputfile.png**, the plot will be saved as a PNG file. The user can set
the output size (in inches) and resolution (dpi) of the output image.

## NOTE

If you work with a large number of raster layers, of if the raster
layers are very large, try to avoid setting the range value very low, as
that may result in a massive number of outliers, slowing down the
computations and rendering of the plot.

## EXAMPLE

The examples use the North Carolina full dataset, which you can download
from
[https://grass.osgeo.org/download/data/#NorthCarolinaDataset](https://grass.osgeo.org/download/data/#NorthCarolinaDataset).

### Example 1

Three landsat layers are provided as input. In addition, plot dimensions
are set to 12 inch wide, 6 inch height.

```sh
r.series.boxplot plot_dimensions=12,6 \
map=lsat7_2002_10,lsat7_2002_20,lsat7_2002_30,lsat7_2002_40,lsat7_2002_50
```

![image-alt](r_series_boxplot_1.png)

### Example 2

The example below uses the same layers as input. In addition, it defines
the colors for the boxplots, rotates the labels and sets the fontsize to
14.

```sh
r.series.boxplot plot_dimensions=12,6 \
map=lsat7_2002_10,lsat7_2002_20,lsat7_2002_30,lsat7_2002_40,lsat7_2002_50 \
bxcolor=green rotate_labels=45 fontsize=14
```

See [(https://matplotlib.org/stable/tutorials/colors/colors.html](https://matplotlib.org/stable/tutorials/colors/colors.html)
for the different formats in which colors can be specified.

![image-alt](r_series_boxplot_2.png)

### Example 3

Same example as above, but this time, the outliers are plotted as well
(in blue). And the labels are explicitly defined.

```sh
r.series.boxplot -o plot_dimensions=12,6 rotate_labels=45 fontsize=14 \
map=lsat7_2002_10,lsat7_2002_20,lsat7_2002_30,lsat7_2002_40,lsat7_2002_50 \
flier_color=blue bxcolor=green \
text_labels="2002 10,2002 20,2002 30,2002 40,2002 50"
```

![image-alt](r_series_boxplot_3.png)

## Acknowledgements

This work was carried in the framework of the [Save the tiger, save the
grassland, save the water](https://savethetiger.nl/) project by the
[Innovative Bio-Monitoring research
group](https://www.has.nl/en/has-research/research-groups/innovative-bio-monitoring-research-group)
of the HAS University of Applied Sciences.

## SEE ALSO

*[r.boxplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.boxplot.html),
[d.vect.colbp](https://grass.osgeo.org/grass-stable/manuals/addons/d.vect.colbp.html),
[r.scatterplot](https://grass.osgeo.org/grass-stable/manuals/addons/r.scatterplot.html),
[r.stats.zonal](https://grass.osgeo.org/grass-stable/manuals/r.stats.zonal.html)*

## AUTHOR

Paulo van Breugel  
Applied Geo-information Sciences  
[HAS University of Applied Sciences](https://www.hasuniversity.nl/)
