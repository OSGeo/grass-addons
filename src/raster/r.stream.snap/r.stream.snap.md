## DESCRIPTION

The module *r.stream.snap* is a supplementary module for
*[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
and *[r.stream.basins](r.stream.basins.md)* to correct the position of
outlets or stream initial points as they do not lie on the streamlines.

For the outlet, the point is snapped to the nearest point which lies on
the streamline.

For the stream initial points, when there is a small tributary near the
main stream, the accumulation threshold shall be high enough to force
the program ignoring this tributary and snap to the main stream. If
there is no accumulation map, the points will be snapped to the nearest
stream line, which in particular situations may be wrong. Because the
*r.stream.\** modules are prepared to work with MFD accumulation maps,
both stream network and accumulation map are necessary.

While it is assumed that the accumulation map is a MFD map, if the
stream network is not supplied, the snap point is calculated in
different way: the threshold is used to select only those points in the
search radius which have accumulation value greater than the given
threshold. The next mean value of these points is calculated and its
value is taken as a new threshold. This procedure guarantees that points
are snapped to the center of the stream tube. While for inits small
thresholds are in use, it is probable that points were snapped to the
stream tube border instead of its center.

It is strongly recommended to use both stream network (even
pre-generated with small accumulation threshold) and accumulation raster
map, than accumulation or stream raster map only.

## OPTIONS

- **stream\_rast**  
    Stream network created by
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
    or
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*.
    If used, the points are snapped to the nearest streamline point
    whose accumulation is greater than the threshold. If the
    accumulation is not used, the point is snapped to the nearest
    stream.
- **accumulation**  
    Accumulation map created with
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*
    and used to generate the stream network with
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*.
    If the stream network is not used, the point is adaptively snapped
    to the point where the value is greater than mean values of
    accumulation greater than given threshold in a search radius. See
    the description for details.
- **radius**  
    Search radius (in cells). If there are no streams in the search
    radius, the point is not snapped. If there are no cells with
    accumulation greater than accumulation threshold, the point also is
    not snapped.
- **threshold**  
    Minimum value of accumulation to snap the point. This option is
    added to the snap stream inits to the stream tubes and to
    distinguish between local tributaries and main streams.
- **input**  
    Vector file containing outlets or inits as vector points. Only
    point's categories are used. Any table attached to it is ignored.
    Every point shall have its own unique category.
- **output**  
    Vector file containing outlets or inits after snapping. On layer 1,
    the original categories are preserved, on layer 2 there are four
    categories which mean:
    1. skipped (not in use yet)
    2. unresolved (points remain unsnapped due to lack of streams in
        search radius
    3. snapped (points snapped to streamlines)
    4. correct (points which remain on their original position, which
        were originally corrected)

## EXAMPLE

```sh
g.region -p -a raster=elevation
r.watershed elevation=elevation threshold=10000 drainage=dirs stream=streams accumulation=accum
# snap a point sampled in the riverine landscape to the calculated river network
r.stream.snap input=mysampleoutlet output=mysampleoutlet_snapped stream_rast=streams accumulation=accum
```

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.basins](r.stream.basins.md),
[r.stream.channel](r.stream.channel.md),
[r.stream.order](r.stream.order.md),
[r.stream.segment](r.stream.segment.md),
[r.stream.slope](r.stream.slope.md),
[r.stream.stats](r.stream.stats.md),
[r.stream.distance](r.stream.distance.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

See also [r.streams.\*
modules](https://grasswiki.osgeo.org/wiki/R.stream.*_modules) wiki page.

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
