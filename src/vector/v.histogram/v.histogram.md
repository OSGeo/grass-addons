## DESCRIPTION

*v.histogram* draws a histogram of the values in a vector map attribute
column. Users can use the **where** option to only select a subset of
the attribute table and can determine the number of **bins** (bars) used
for the histogram. The **plot\_output** parameter determines whether the
result is displayed on screen (default) or exported to a graphics file.

## NOTE

This is a quick and dirty solution using basic matplotlib. In future,
this should be integrated into the g.gui, possibly together with the
raster histogram tool.

## EXAMPLE

Show the histogram of median age values in the census block map:

```sh
v.histogram map=censusblk_swwake column=MEDIAN_AGE where="TOTAL_POP>0"
```

![image-alt](d_vect_colhist.png)  
Histogram of median age values in census blocks

## AUTHOR

Moritz Lennert
