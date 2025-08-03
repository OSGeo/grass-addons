## DESCRIPTION

*r.vect.stats* bins points from a vector map into a raster map.

Use
*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*
to set the extent and resolution of the resulting raster.

## EXAMPLES

Calculate number of schools in grid of spatial resolution 1km:

```sh
g.region res=1000 vector=schools_wake
r.vect.stats input=schools_wake output=schools_count
```

Calculate sum of atribute column CAPACITYTO:

```sh
r.vect.stats input=schools_wake output=schools_capacity_sum column=CAPACITYTO method=sum
```

![image-alt](r_to_vect_schools_count.png)
![image-alt](r_to_vect_schools_sum.png)  
*Figure: Number of schools (left part) and sum of CAPACITYTO attribute
column (right part) in grid of spatial resolution 1km.*

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[v.out.ascii](https://grass.osgeo.org/grass-stable/manuals/v.out.ascii.html),
[r.in.xyz](https://grass.osgeo.org/grass-stable/manuals/r.in.xyz.html),
[r.in.lidar](https://grass.osgeo.org/grass-stable/manuals/r.in.lidar.html)*

## AUTHORS

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)  
Column and method parameters added by Martin Landa, [CTU GeoForAll
Lab](https://geomatics.fsv.cvut.cz/research/geoforall/)
