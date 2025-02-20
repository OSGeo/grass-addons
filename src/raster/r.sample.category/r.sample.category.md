## DESCRIPTION

*r.sample.category* generates points at random locations. Each category
(class) in a raster map will contain specified number of random points.

Different number of points can be specified for different categories.
For example, if there are categories 1, 4, 7 in the input raster map,
and npoints=100,200,300, 100 points will be generated in category 1, 200
points in category 4 and 300 points in category 7. If only one number is
specified, it will be used for every category.

## NOTES

Mask
(*[r.mask](https://grass.osgeo.org/grass-stable/manuals/r.mask.html)*)
to create points in areas with each category, thus mask cannot be active
when the module is used.

Categories are identified based on current computational region.

## EXAMPLE

### Generate random points

Generate three points at random location for each category (class) in
the raster map:

```sh
g.region raster=landclass96
r.sample.category input=landclass96 output=landclass_points npoints=3
```

Show the result:

```sh
d.rast map=landclass96
d.vect map=landclass_points icon=basic/circle fill_color=aqua color=blue size=10
```

![image-alt](r.sample.category.png)  
Figure: Three random points in each category of landclass raster map

### Create a table with values sampled from rasters

Create 2 random points per each category (class) in landclass96 raster
and sample elevation and geology\_30m rasters at these points:

```sh
r.sample.category input=landclass96 output=landclass_points sampled=elevation,geology_30m npoints=2
```

Look at the created data:

```sh
v.db.select landclass_points sep=comma
```

The result of
*[v.db.select](https://grass.osgeo.org/grass-stable/manuals/v.db.select.html)*
is CSV table which can be used, for example in a spreadsheet
application:

```sh
cat,landclass96,elevation,geology_30m
1,1,102.7855,270
2,1,105.78,270
3,2,114.5954,217
4,2,137.4816,921
5,3,71.19167,270
6,3,93.33904,270
7,4,76.41077,262
8,4,97.54424,217
9,5,138.455,405
10,5,88.8075,270
11,6,126.5298,217
12,6,86.73177,217
13,7,134.5381,217
14,7,99.6844,270
```

## SEE ALSO

*[v.sample](https://grass.osgeo.org/grass-stable/manuals/v.sample.html),
[r.random](https://grass.osgeo.org/grass-stable/manuals/r.random.html),
[r.random.cells](https://grass.osgeo.org/grass-stable/manuals/r.random.cells.html),
[v.random](https://grass.osgeo.org/grass-stable/manuals/v.random.html),
[v.what.rast](https://grass.osgeo.org/grass-stable/manuals/v.what.rast.html),
[r.describe](https://grass.osgeo.org/grass-stable/manuals/r.describe.html)*

## AUTHORS

Vaclav Petras, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/),  
Anna Petrasova, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/)
