## DESCRIPTION

The tool derives single elevation value for water bodies based on lidar
data. These values are used for hydro-flattening a digital elevation
model. The **input** raster is expected to represent ground surface
created by binning lidar data (e.g., using *[r.in.pdal](r.in.pdal.md)*)
with averaged ground elevation. Small gaps in the input are expected.
Large gaps are interpreted as water bodies. The minimum size of a water
body can be set with **min\_size** option in map units.

The output **water\_elevation** is a raster map of water bodies where
each water body has a single value representing the water level
elevation derived from the lidar data at the edge of a water body. Since
the elevation varies along the edge, option **percentile** is used to
determine a single value. The variation along the edge can be examined
with the **water\_elevation\_stddev** output representing the standard
deviation of the lidar elevation values along the water body's edge.
Higher deviation suggests problematic areas that need to be further
inspected. The optional output **filled\_elevation** is a raster map of
the input ground surface filled with the computed **water\_elevation**
raster map.

The **breaklines** parameter is an optional input that specifies a
vector map of lines that represent e.g., a break between an impoundment
and downstream river, allowing correct elevation computation.

To keep the intermediate results for inspection, use flag **-k**.

## NOTES

While this tool was designed for water bodies, it can be used for other
purposes, e.g., for filling a gap in digital elevation models caused by
excluding buildings.

This tool does not interpolate gaps in data, rather it derives a single
value for each gap. The result can be used to fill gaps and the tool can
be run on large areas. For actual gap interpolation, which is typically
more computationally intensive, see
*[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnuls.html)*.

## EXAMPLE

We will download a lidar tile with *[r.in.usgs](r.in.usgs.md)* addon,
use
*[r.in.pdal](https://grass.osgeo.org/grass-stable/manuals/r.in.pdal.html)*
to bin the elevation points at 1 meter resolution, and derive elevation
levels for lakes with minimum size of 4000 m^2.

```sh
# select study area and resolution
g.region n=213300 s=211900 w=653900 e=655300 res=1
# download lidar tile into /tmp
r.in.usgs product=lidar output_directory=/tmp title_filter=Phase2 -d
# bin point elevation using ground and road points with reprojection
r.in.pdal input=/tmp/USGS_LPC_NC_Phase2_2014_LA_37_20164902_.laz output=ground -w class_filter=2,13
# convert elevation from feet to meters
r.mapcalc "ground_m = ground * 0.304800609601219"
# derive elevation of water bodies and standard deviation
r.hydro.flatten input=ground_m water_elevation=water_elevation water_elevation_stddev=water_elevation_stddev filled_elevation=filled percentile=10 misize=4000
```

![image-alt](r_hydro_flatten_input.png)
![image-alt](r_hydro_flatten_output_elevation.png)
![image-alt](r_hydro_flatten_output_stddev.png)  
*Figure: Input binned elevation representing ground with gaps (left),
input overlayed with elevation values estimated for gaps and highlighted
with an outline (middle), input overlayed with standard deviation of the
elevation along the edge of the gaps (right).*

## REFERENCE

Method based on workflow
[presented](https://www.youtube.com/watch?v=p9KCfufNYgE) at NC GIS
Conference 2021 by Doug Newcomb.

## SEE ALSO

*[r.in.pdal](https://grass.osgeo.org/grass-stable/manuals/r.in.pdal.html),
[r.in.usgs](r.in.usgs.md),
[r.fillnulls](https://grass.osgeo.org/grass-stable/manuals/r.fillnulls.html)*

## AUTHOR

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
