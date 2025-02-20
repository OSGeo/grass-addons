## DESCRIPTION

*v.surf.mass* creates a raster surface from vector areas, preserving the
value of the area attribute. For example, if the selected area attibute
is the population count, the sum of all pixel values in a given area is
equal to the area's population count.

## NOTES

The current region needs to be prepared with
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
choosing a resolution such that the smallest area is covered by at least
four pixels. The current region should be completely inside the bounding
box of the vector.

## EXAMPLE

### Pycnophylactic interpolation of Voronoi triangles using annual precipitation in the North Carolina sample data

(see below for screenshots of the results)

```sh
# setting the region
g.region -p raster=elev_state_500m

# create Voronoi diagram based on meteorological stations
v.voronoi input=precip_30ynormals output=precip_annual

# List of attributes for the vector precip_annual
v.info -c precip_annual

# v.surf.mass converts attributes to density, but rainfall is
# typically measured in mm which is the same for all cells in the
# same input area, thus:
# new column for area size and adjusted precipitation
v.db.addcolumn map=precip_annual \
     column="area double precision, prec_adj double precision"
v.to.db map=precip_annual column=area option=area units=meters

# Getting the size of the smallest area
v.db.univar precip_annual column=area

# The smallest area with some population is 1.20789e+08 square meters
# and with a resolution of 5000 meters covered by appr. four pixels
# (depending on the shape of the area). Adjust region for that:
g.region res=5000 -ap

# adjust precipitation values: multiply by area size, dived by pixel size
v.db.update map=precip_annual column=prec_adj \
     qcolumn="annual * area / 25000000"

# mass-preserving area interpolation
v.surf.mass input=precip_annual output=precip_annual_pycno column=prec_adj iterations=200

# rasterize Voronoi diagram for comparison
v.to.rast precip_annual out=precip_annual_voronoi type=area use=attr attrcolumn=annual

# verify results
d.mon wx0
d.rast.leg precip_annual_voronoi
d.rast.leg precip_annual_pycno
```

![image-alt](v_surf_mass_voronoi.png)  
*Annual precipitation (30 years avg.) of North Carolina shown as Voronoi
diagram based on meteorological stations (perspective view in NVIZ).*
![image-alt](v_surf_mass_pycno.png)  
*Smooth Pycnophylactic Interpolation of annual precipitation (30 years
avg.) of North Carolina using the Voronoi diagram map based on
meteorological stations (perspective view in NVIZ).*

## REFERENCES

Tobler WR. 1979. Smooth Pycnophylactic Interpolation for Geographical
Regions. Journal of the American Statistical Association, 74 (367):
519-530
([PDF](https://people.geog.ucsb.edu/~kclarke/Geography232/Pycno.pdf)).

## AUTHOR

Markus Metz
