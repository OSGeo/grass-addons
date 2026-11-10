## DESCRIPTION

*v.vol.idw* fills a RASTER3D raster volume matrix with interpolated
values generated from a set of irregularly spaced data points using
numerical approximation (weighted averaging) techniques. The
interpolated value of a tile is determined by values of nearby data
points and the distance of the cell from those input points. In
comparison with other methods, numerical approximation allows
representation of more complex volumes (particularly those with
anomalous features), restricts the spatial influence of any errors, and
generates the interpolated volume from the data points.

## EXAMPLE

```sh
v.vol.idw input=map output=rastermap3d column=col_name npoints=36
```

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[v.in.ascii](https://grass.osgeo.org/grass-stable/manuals/v.in.ascii.html),
[v.in.db](https://grass.osgeo.org/grass-stable/manuals/v.in.db.html),
[v.surf.idw](https://grass.osgeo.org/grass-stable/manuals/v.surf.idw.html),
[v.vol.rst](https://grass.osgeo.org/grass-stable/manuals/v.vol.rst.html),
[v.to.rast3](https://grass.osgeo.org/grass-stable/manuals/v.to.rast3.html)*

## AUTHOR

Jaro Hofierka, Department of Geography and Regional Development,
University of Presov, Presov, Slovakia, <hofierka@geomodel.sk>  

Modifications for raster3d library and vector format:  
Noortheen Raja J, Institute of Remote Sensing, College of Engineering,
Guindy, Anna University, India. <jnoortheen@gmail.com>
