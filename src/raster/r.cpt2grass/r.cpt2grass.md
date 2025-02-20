## DESCRIPTION

Module *r.cpt2grass* converts [GMT](http://gmt.soest.hawaii.edu/) color
palette (\*.cpt) format to GRASS color table format and assigns it to a
given raster map. Input can be either cpt file given in **input** option
or a URL of the cpt file specified in **url** option. Specifying URL is
particularly useful when using color tables from
[cpt-city](http://soliton.vm.bytemark.co.uk/pub/cpt-city/), because many
color tables can be quickly tested without downloading the files. When
option **map** is specified *r.cpt2grass* assigns the color rules to the
given raster map. Depending on the values of the original cpt file, it
may be advantageous to use the **-s** to stretch the colors based on the
range of values of the map.

## NOTES

RGB and HSV models are supported. The expected format of the cpt file
is:

```sh
# COLOR_MODEL = RGB
value1 R G B value2 R G B
value2 R G B value3 R G B
...
```

Named colors are not supported.

## EXAMPLES

From [cpt-city](http://soliton.vm.bytemark.co.uk/pub/cpt-city/) we
download a
[rainfall](http://soliton.vm.bytemark.co.uk/pub/cpt-city/jjg/misc/rainfall.cpt)
color table and convert it to GRASS color table. If we don't specify
output file, it is printed to standard output:

```sh
r.cpt2grass input=rainfall.cpt
```

```sh
0.000 229:180:44
20.000 229:180:44
20.000 242:180:100
40.000 242:180:100
40.000 243:233:119
60.000 243:233:119
60.000 145:206:126
80.000 145:206:126
80.000 67:190:135
100.000 67:190:135
100.000 52:180:133
120.000 52:180:133
120.000 6:155:66
140.000 6:155:66
```

We set two different elevation color tables - continuous and discrete
gradients. We have to stretch the color tables to fit the raster map
range:

```sh
r.cpt2grass url=http://soliton.vm.bytemark.co.uk/pub/cpt-city/td/DEM_screen.cpt map=elevation -s
r.cpt2grass url=http://soliton.vm.bytemark.co.uk/pub/cpt-city/cb/seq/YlOrBr_09.cpt map=elevation -s
```

We can display legend:

```sh
d.legend raster=elevation labelnum=10 at=5,50,7,10
```

![image-alt](r_cpt2grass_color_table_DEM_screen.png)
![image-alt](r_cpt2grass_color_table_YlOrBr_09.png)

## SEE ALSO

*[r.colors](https://grass.osgeo.org/grass-stable/manuals/r.colors.html)*

## AUTHORS

Anna Petrasova, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/)  
Hamish Bowman (original Bash script)
