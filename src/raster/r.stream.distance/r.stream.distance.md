## DESCRIPTION

The module *r.stream.distance* can calculate: the distance to streams;
the distance to outlet; the relative elevation above streams; the
relative elevation above the outlet. The distance and the elevation are
calculated along watercourses.

The module may calculate the distance either *downstream* or *upstream*.
The default is set on downstream. The upstream method calculates the
distance to the local maximum or divide. Opposite to downstream method,
where every cell has one and only one downstream cell, in upstream
method every cell has usually more than one upstream cell. So it is
impossible to determine interchangeable path from any cell.

The upstream method offers two alternative modes switched with *-n*
flag: the *nearest local maximum/divide* is the shortest path to the
local maximum; and the *farthest maximum/divide* is the longest path
(default option). In hydrological sense, the *nearest* option means the
shortest path which a particle of water must run from the divide to
reach a particular pixel, while the *farthest* option means the possible
longest path.

In *outlets* mode, the module can optionally be used for subbasins.

In *streams* mode (default) it calculates the distance (downstream) to
the stream network taken in input. In *outlets* mode there are some
additional possibilities. If the *subbasin* option is set off, it
calculates the distance only for the outlet (downstream). If the
*subbasin* option is set on, it calculates the distance to outlet for
every subbasin separately. The *subbasin* option acts similarly to a
subbasin mask. The module *r.stream.basins* can be used to prepare the
stream network map taken in input by *r.stream.distance*. In fact it can
be used to individuate basins and subbasins.

In lat-long locations, the module gives distances not in degrees but in
meters.

## OPTIONS

- **-o**  
    Outlets. Downstream method only. Calculate distance to or elevation
    above the outlet instead of streams. It chooses only the last outlet
    in the network ignoring nodes.
- **-s**  
    Subbasins. Downstream method only. Calculate distance to or
    elevation above stream nodes instead of streams. The distance and
    the elevation difference are relative to elementary subbasins
    instead of the whole basin.
- **-n**  
    Near. For upstream method only. Calculate distance to or elevation
    above the nearest local maximum/divide. With the default option, the
    distance/elevation is calculated to the farthest possible
    maximum/divide.
- **stream\_rast**  
    Stream network: name of input stream network map, produced using
    either *r.watershed* or *r.stream.extract*. Since stream network
    maps produced by *r.watershed* and *r.stream.extract* may slightly
    differ in detail, it is required to use both stream and direction
    maps produced by the same module. Non-stream cell values must be set
    to NULL. Alternatively, in *outlet* mode, it's the raster map of the
    outlet.
- **direction**  
    Flow direction: name of input raster map with flow direction,
    produced using either *r.watershed* or *r.stream.extract*. If
    *r.stream.extract* output map is used, it is non-NULL only where
    streams occur and NULL elsewhere. NULL (nodata) cells are ignored,
    zero and negative values are valid direction data only if they vary
    from -8 to 8 (CCW from East in steps of 45 degrees). Flow direction
    map shall be of integer type (CELL).
- **elevation**  
    Elevation: name of input elevation map. It can be of type CELL,
    FCELL or DCELL.
- **method**  
    It is possible to calculate the distance with two method:
    **downstream** from any raster cell to the nearest stream cell /
    junction cell or outlet or **upstream** from any cell upstream to
    the nearest maximum or divide.
- **difference**  
    Name of output map of elevation difference to the target (outlet,
    node, stream, divide, maximum) along watercoures. The map is of
    DCELL type.
- **distance**  
    Name of output map of distance to the target (outlet, node, stream,
    divide, maximum) along watercoures. The map is of DCELL type.

## NOTES

In *stream* mode subbasin options is omitted. Input maps must be in CELL
format (default output of *r.watershed*, *r.stream.order* and
*r.stream.extract*). The distance is calculated in meters, for flat
areas not corrected by topography. Distance correction by topography may
be done using the following *r.mapcalc* formula:

```sh
r.mapcalc expression = "dist_corrected = sqrt(distance^2 + elevation^2)"
```

The module can work only if direction map, streams map and region have
the same settings. This is checked by default. If resolutions differ,
the module informs about it and stops. Region boundary and maps boundary
may differ but it may lead to unexpected results. The elevation map is
not affected by this restriction and can have whatever resolution.

It is also required that *stream\_rast* and *direction* maps come from
the same source, e.g. both from *r.stream.extract*. If the stream
network was generated with MFD method also MFD direction map must be
used.

Probably one of the most important features of *r.stream.distance* is
the ability to calculate the distance not only for streams generated by
*r.stream.extract*, but also for any integer map, as long as the
resolution corresponds to that of *direction* map. It can be a lake,
swamp, depression and lake boundaries even divided into smaller
fragments each with its own category.

## EXAMPLE

```sh

# Set the region to match with elevation map
g.region -pa raster=elevation

# Calculate flow direction and stream network
r.watershed elevation=elevation threshold=10000 drainage=direction stream=streams

# Calculate elevation above and distance to stream network using downstream method
r.stream.distance stream_rast=streams direction=direction elevation=elevation \
  method=downstream distance=distance_stream_downstream difference=difference_stream_downstream

# Calculate elevation above and distance to stream network using upstream method
r.stream.distance stream_rast=streams direction=direction elevation=elevation \
  method=upstream distance=distance_stream_upstream difference=difference_stream_upstream

# Create outlet
echo "636645,218835" | v.in.ascii -n input=- output=outlet separator=","

# Convert outlet to raster
v.to.rast input=outlet output=outlet use=cat

# Calculate distance to and elevation above outlet
r.stream.distance -o stream_rast=outlet direction=direction elevation=elevation \
  method=downstream distance=distance2outlet difference=difference2outlet

```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html),
[r.stream.channel](r.stream.channel.md),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.order](r.stream.order.md),
[r.stream.segment](r.stream.segment.md),
[r.stream.slope](r.stream.slope.md), [r.stream.snap](r.stream.snap.md),
[r.stream.stats](r.stream.stats.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

See also [r.streams.\*
modules](https://grasswiki.osgeo.org/wiki/R.stream.*_modules) wiki page.

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
