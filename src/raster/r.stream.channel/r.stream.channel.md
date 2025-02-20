## DESCRIPTION

The module *r.stream.channel* is prepared to calculate some local
properties of the stream network. It is supplementary module for
*r.stream.order*, and *r.stream.distance* to investigate channel
subsystem. For slope subsystem parameters is *r.stream.slope*. It may
use ordered or unordered network. It calculate parameters for every
segment between it init to outlet/join to the next stream. it also may
calculate parameters between outlet and segment's init. It can calculate
parameters for every orders but best results are for these orders where
order remains unchanged from stream init to natural outlet (Hack and
Horton ordering).

## OPTIONS

  - **-d**  
    Calculate downstream distance (from current cell DOWNSTREAM to
    outlet/join). Default is upstream (from current cell upstream to
    init/join.
  - **-m**  
    Only for very large data sets. Uses segment library to optimize
    memory consumption during analysis
  - **stream\_rast**  
    Stream network: name of input stream map. Map may be ordered
    according to one of the *r.stream.order* ordering systems as well as
    unordered (with original stream identifiers). Because the streams
    network produced by *r.watershed* and *r.stream.extract* may
    slightly differ in detail it is required to use both stream and
    direction map produced by the same module. Non-stream cell values
    must be set to NULL.
  - **direction**  
    Flow direction: name of input direction map produced by
    *r.watershed* or *r.stream.extract*. If the *r.stream.extract*
    output map is used, it contains non-NULL values only in places where
    streams are present. NULL cells are ignored; zero and negative
    values are valid direction data if they vary from -8 to 8 (CCW from
    East in steps of 45 degrees). The direction map shall be of integer
    type (CELL). The region resolution and map resolution must be the
    same. Also the *stream\_rast* network map must have the same
    resolution. If resolutions differ the module informs about it and
    stops. Region boundary and maps boundary may be different but it may
    lead to unexpected results.
  - **elevation**  
    Elevation: name of input elevation map. Map can be of type CELL,
    FCELL or DCELL. It is not restricted to resolution of region
    settings as streams and direction.
  - **distance**  
    Upstream distance of current cell to the init/join. Flag
    modifications:  
    **-d:** downstream distance of current cell to the join/outlet;  
    **-l:** local distance between current cell and next cell. In most
    cases cell resolution and sqrt2 of cell resolution. useful when
    projection is LL or NS and WE resolutions differs. Flag **-d**
    ignored  
    **-c:** distance in cells. Map is written as double. Use *r.mapcalc*
    to convert to integer. Flags **-l** and **-d** ignored.  
  - **difference**  
    Upstream elevation difference between current cell to the init/join.
    It we need to calculate parameters different than elevation. If we
    need to calculate different parameters than elevation along streams
    (for example precipitation or so) use necessary map as elevation.
    Flag modifications:  
    **-d:** downstream difference of current cell to the join/outlet;  
    **-l:** local difference between current cell and next cell. With
    flag calculates difference between previous cell and current cell  
    **-c:** Ignored.
  - **gradient**  
    Upstream mean gradient between current cell and the init/join. Flag
    modifications:  
    **-d:** downstream mean gradient between current cell and the
    join/outlet;  
    **-l:** local gradient between current cell and next cell. Flag
    **-d** ignored  
    **-c:** Ignored.
  - **curvature**  
    Local stream course curvature of current cell. Calculated according
    formula:
    *first\_derivative/(1-second\_derivative<sup>2</sup>)<sup>3/2</sup>*
    Flag modifications:  
    **-d:** ignored;  
    **-l:** Ignored.  
    **-c:** Ignored.
  - **identifier**  
    Integer map: In ordered stream network there are more than one
    segment (segment: a part of the network where order remains
    unchanged) with the same order. To identify particular segments (for
    further analysis) every segment receive his unique identifier.

## EXAMPLE

This example shows how to visualise the change of gradient map along the
main stream of the catchment:

```sh
g.region -p -a raster=elevation
r.watershed elevation=elevation threshold=10000 drainage=direction stream=streams
r.stream.order streams=streams direction=direction hack=hack
r.stream.channel streams=hack direction=direction elevation=elevation \
  identifier=stream_identifier distance=stream_distance gradient=stream_gradient

# Eg., 495 is a stream identifier. May be different in different situation
r.mapcalc "stgrad = if(stream_identifier==495,float(stream_gradient),null())"
r.mapcalc "stdist = if(stream_identifier==495,float(stream_distance),null())"

# Use R for plotting
R
library(spgrass6)
r=readRAST6(c("stdist","stgrad"),NODATA=-9999)
p=subset(r@data,!is.na(r@data$dist))
sorted=p[order(p$stdist),]
plot(sorted,stdist~stgrad,type="l")
```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.stream.distance](r.stream.distance.md),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.order](r.stream.order.md),
[r.stream.basins](r.stream.basins.md),
[r.stream.segment](r.stream.segment.md),
[r.stream.slope](r.stream.slope.md), [r.stream.snap](r.stream.snap.md),
[r.stream.stats](r.stream.stats.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
