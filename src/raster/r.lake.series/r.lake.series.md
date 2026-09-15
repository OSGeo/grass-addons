## DESCRIPTION

***r.lake.series*** fills a lake or any area from a given start point or
areas specified by raster map (`seed_raster` option). The module
generates one map containing filled areas for each water level specified
by water level options (`start_water_level`, `end_water_level`,
`water_level_step`). This module uses
*[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)*
module to generate individual maps for the map series. See
*[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)*
manual for further discussion. Note that water level is absolute height,
so it should be in same range as you digital elevation model. On the
other hand, water depth in output maps is relative to the water level.

This module outputs:

- a space-time raster dataset containing a map series
- a map series containing maps of areas with water for each water
    level

## EXAMPLE

The following example presents a bigger flooding in rural area of North
Carolina sample dataset and included also visualization examples.

```sh
# using unix-like shell syntax

# set computational region
g.region raster=elev_lid792_1m
# prepare input data
v.to.rast -d input=streams output=rural_streams use=val val=1

# compute a flooding scenario
r.lake.series elevation=elev_lid792_1m seed=rural_streams \
              start_wl=104.0 end_wl=115.0 wl_step=0.2 output=flooding

# visualize the flooding space-time raster dataset
g.gui.animation strds=flooding

# alternatively explore maps from dataset
# prepare shaded relief map
r.relief input=elev_lid792_1m output=elev_lid792_1m_shade
# set color table for streams
r.colors map=rural_streams rules=- <<EOF
1 blue
EOF

# open d.mon or map display
d.mon wx1

# show base maps
d.rast elev_lid792_1m_shade
d.rast rural_streams

# show particular flooding maps
d.rast flooding_105.0
d.rast flooding_108.0
d.rast flooding_114.0
```

![image-alt](rural_flooding_105.jpg)
![image-alt](rural_flooding_108.jpg) ![image-alt](r.lake.series.jpg)

Figure: A bigger flooding in rural area of North Carolina sample dataset
with water level at 105, 108 and 114 meters (water depth differs in
different areas).

## SEE ALSO

*[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)*

## AUTHORS

Vaclav Petras, [NCSU OSGeoREL](http://gis.ncsu.edu/osgeorel/),  
Maris Nartiss (author of
*[r.lake](https://grass.osgeo.org/grass-stable/manuals/r.lake.html)*)
