## DESCRIPTION

The module *r.stream.basins* is prepared to delineate basins and
subbasins with different input data. The module is prepared to delineate
an unrestricted number of basins in one step. It can delineate basins
with three methods:

  - Using coordinates: this option performs the same operation as
    *r.water.outlet*.
  - Using vector points: it allows to manually point outlets with any
    method.
  - Using streams (most advanced): it allows broader functionalities:
    See the examples for more details.

Only one method can be used at once: the methods cannot be mixed.

The recommended method requires two maps: flow direction and streams.
Using cats option it is possible to create basins having the same
category of the stream they refer to. The module is prepared to work
with output data of *r.watershed*, *r.stream.extract*, *r.stream.order*
also with modification done by *r.reclass* and *r.mapcalc*.
*r.stream.basins* can delineate basins according outlets marked by
raster streams, polygons, vector points or coordinates. If the outlets
are given by points or coordinates, the module delineates the basins
individuating the cells that drain into that point. If the outlets are
marked by the streams, it includes the cells that contribute to the last
(downstream) cell of each stream. If the outlets are marked by polygons,
it includes the cells contributing to the most downstream cell of the
polygon. If the polygon covers more outlets than of one basins, it will
create a collective basin for all the outlets with common category.

## OPTIONS

  - **-z**  
    Creates zero-value background instead of NULL. For some reason (like
    map algebra calculation) zero-valued background may be required.
  - **-c**  
    By default *r.stream.basins* uses streams category as basin
    category. In some cases - for example if streams map is a product of
    map algebra and separate streams may not have unique values - this
    option will create a new category sequence for each basin (it does
    not work in vector point mode).
  - **-l**  
    By default *r.stream.basins* creates basins for all unique streams.
    This option delineates basins only for the last streams, ignoring
    upstream (it does not work in vector point mode).
  - **direction**  
    Flow direction: name of input flow direction map produced by
    *r.watershed* or *r.stream.extract*. The resolution of the
    computational region must match with the resolution of the raster
    map. Also the *stream* network map (if used) and the direction map
    must have the same resolution. It is checked by default. If
    resolutions differ, the module informs about it and stops. Region
    boundary and maps boundaries may differ but it may lead to
    unexpected results.
  - **coors**  
    East and north coordinates for the basin outlet. Using this option,
    it is possible to delineate only one basin at a time, similarly to
    *r.water.outlet*.
  - **stream\_rast**  
    Stream network: name of input map of stream network, ordered
    according to the convention used by *r.watershed* or
    *r.stream.extract*. Since streams network produced by *r.watershed*
    and *r.stream.extract* might slightly differ in detail, it is
    required to use both stream and direction map produced by the same
    module. The stream background can have either NULL or zero values.
  - **cats**  
    Stream categories to delineate basins for: All categories which are
    not in the stream map are ignored. It is possible to use the stream
    network created by *r.watershed*, *r.stream.extract* or
    *r.stream.order*. For *r.stream.order*, it is possible to select the
    order for which basins will be created. For example, to delineate
    only basins for the streams of second order, use **cats=2**. If you
    need unique categories for each basin, use **-c** flag.
  - **points**  
    Vector file containing basins outlets as vector points. Only points'
    categories are used to delineate the basins. Attached tables are
    ignored. Every point shall have its own unique category. In this
    mode, flags **-l** and **-c** are ignored.

## OUTPUTS

The module produces one raster map with basins defined according to the
user's rules.

## NOTES

To achieve good results, outlets markers created by the user shall
overlap with the streams, otherwise basins could result with very small
area. Input maps must be in CELL format (default output of
*r.watershed*, *r.stream.order* or *r.stream.extract*).

## EXAMPLES

To delineate all basins with categories of streams:

```sh
r.stream.basins direction=direction stream_rast=streams basins=bas_basins_elem
```

To determine major and minor basins defined by outlets, ignoring
subbasins, use -l flag. This flag ignores all nodes and uses only real
outlets (in most cases that on map border):

```sh
r.stream.basins -l direction=direction stream_rast=streams basins=bas_basins_last

r.stream.basins direction=direction coors=639936.623832,216939.836449
```

To delineate one or more particular basins defined by given streams, add
simply stream categories:

```sh
r.stream.basins -lc direction=direction stream_rast=streams cats=2,7,184 basins=bas_basin
```

To delineate basins of particular order, the following procedure can be
used:

```sh
r.stream.basins -lc direction=direction stream_rast=strahler cats=2 \
  basins=bas_basin_strahler_2
```

The usage of polygons as outlets markers is useful when the exact stream
course cannot be clearly determined before running the analysis, but the
area of its occurrence can be determined (mainly by iterative
simulations). In the example, *r.circle* is used, but it can be
substituted by any polygon created for example with *v.digit*:

```sh
r.circle -b output=circle coordinate=639936.623832,216939.836449 max=200
r.stream.basins -c direction=direction streams=circle basins=bas_simul
```

To determine areas of contribution to streams of particular order use as
streams the result of ordering:

```sh
r.stream.basins direction=direction stream_rast=ord_strahler basins=bas_basin_strahler
```

Determination of areas of potential source of pollution. The example
will be done for lake marked with FULL\_HYDR 8056 in North Carolina
sample dataset. The lake shall be extracted and converted to binary
raster map.

```sh
v.extract -d input=lakes@PERMANENT output=lake8056 type=area layer=1 \
  where='FULL_HYDRO = 8056' new=-1

v.to.rast input=lake8056 output=lake8056 use=val type=area layer=1 value=1

r.stream.basins direction=direction streams=lake8056 basins=bas_basin_lake
```

See also the tutorial: <https://grass.osgeo.org/wiki/R.stream.*>

## SEE ALSO

*[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.order](r.stream.order.md),
[r.stream.stats](r.stream.stats.md),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.reclass](https://grass.osgeo.org/grass-stable/manuals/r.reclass.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html)
[r.water.outlet](https://grass.osgeo.org/grass-stable/manuals/r.water.outlet.html)*

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
