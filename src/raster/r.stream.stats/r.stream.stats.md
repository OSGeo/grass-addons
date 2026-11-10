## DESCRIPTION

The module *r.stream.stats* is prepared to calculate Horton's statistics
of drainage network.

## OPTIONS

- **-c**  
    Print only catchment's characteristics. Useful for shell script
    calculation or collecting data in external tables.
- **-o**  
    Print only parameters for every order. Useful to visualise Horton's
    law with external software (see example bellow).
- **-m**  
    Only for very large data sets. Use segment library to optimise
    memory consumption during analysis.
- **stream\_rast**  
    Stream network: name of input stream raster map produced by
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*
    or
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*,
    on which ordering will be performed. Because stream network produced
    by
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*
    and
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
    may slighty differ in detail, it is required to use both
    **stream\_rast** and direction map produced by the same module. The
    **stream\_rast** background shall have NULL value or zero value.
    Background values of NULL are by default produced by
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*
    and
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*.
    If not 0 or NULL use
    *[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*
    to set background values to NULL.
- **direction**  
    Flow direction: name of input direction raster map produced by
    *[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*
    or
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*.
    If
    *[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
    output raster map is used, it only has non-NULL values in places
    where streams occur. NULL (nodata) cells are ignored, zero and
    negative values are valid direction data if they vary from -8 to 8
    (CCW from East in steps of 45 degrees). Direction map shall be of
    type CELL values. Region resolution and map resolution must be the
    same. Also **stream\_rast** network map must have the same
    resolution. It is checked by default. If resolutions differ the
    module informs about it and stops. Region boundary and maps boundary
    may differ but it may lead to unexpected results.
- **elevation**  
    Elevation: name of input elevation map. Map can be of type CELL,
    FCELL or DCELL. It is not restricted to resolution of region
    settings as **stream\_rast** and **direction** raster map.

### OUTPUTS

Output statistics are send to standard output or to a file if specified
using the **output** option. Aletrnatively, to redirect output to a file
use redirection operators: `>` or `>>` (Unix only). If redirection is
used, output messages are printed on stderr (usually terminal) while
statistics are written to the file. Statistics can be print as a
formatted summary information with number of parameters or as a
catchement's descriptive statistics and table with statistics for every
order.

## NOTES

These statistics are calculated according to formulas given by R. Horton
(1945). Horton didn't define precisely what is stream slope,
consequently 2 different approaches have been proposed. The first
(slope) uses cell-by-cell slope calculation. The second (gradient) uses
the difference between elevation of outlet and source of every channel
to its length to calculate formula. Bifurcation ratio for every order is
calculated acording to the formula: `n_streams[1]/n_stream[i+1]` where
`i` is the current order and `i+1` is the next higher order. For max
order of the cell value of streams is zero. Rest of the ratios are
calculated in similar mode. The bifurcation and other ratios for the
whole catchment (map) is calculated as mean i.e. sum of all bifurcation
`ratio / max_order-1` (for max\_order stream bifurcation `ratio = 0`).
It is strongly recommended to extract the stream network using basin map
created with *r.stream.basins*. If the whole stream order raster map is
used, the calculation will be performed but results may not have
hydrological sense. For every order (std) means that statistics are
calculated with standard deviation:

- number of streams
- total length of streams of a given order
- total area of basins of a given order
- drainage density
- stream density
- average length of streams of a given order (std)
- average slope (cell by cell inclination) of streams of a given order
    (std)
- average gradient (spring to outlet inclination) of streams of a
    given order (std)
- average area of basins of a given order (std)
- avarage elevation difference of a given order (std)

Ratios:

- bifuracation ratio
- length ratio
- slope and gradient ratios
- area ratio

For the whole basin:

- total number of streams
- total length of streams
- total basin area
- drainage density
- stream density

Ratios:

- bifurcation ratio (std)
- length ratio (std)
- slope and gradient ratios (std)
- area ratio (std)

For the whole basins ratios are calculated acording two formulas: as a
mean of ratios for every order, or as a antilog of slope coefficient of
the regression model: order vs. `log10(parameter)`

The module calculates statistics for all streams in input
**stream\_rast** map. It is strongly recommended to extract only network
of one basin, but it is not necessary for computation. Streams for the
desired basin can be extracted by the following
*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html)*
formula:

```sh
# xxx denotes the category of desired basin
r.mapcalc "sel_streams = if(basin == xxx, streams, null())"
```

It is also possible to calculate Horton's statistics for Shreve ordering
but it has no hydrological sense. Hack (or Gravelius hierarchy) main
stream is not the same what so called Horton's reverse ordering (see
Horton 1945).

The module can work only if **direction** raster map, **stream\_rast**
map and region have the same settings. It is also required that
**stream\_rast** map and direction map come from the same source. For
lots of reason this limitation probably cannot be omitted. This means
that if **stream\_rast** map comes from
*[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
also direction map from
*[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html)*
must be used. If the stream network was generated with MFD method also
MFD direction map must be used.

## EXAMPLE

Create table with order statistics. This table can easily be sent to
external program (like R) to be visualized (assuming a unix-like command
line):

```sh
g.region -p -a raster=elevation
r.watershed elevation=elevation threshold=10000 drainage=direction stream=streams
r.stream.stats stream_rast=horton direction=direction elevation=elevation
# export for processing in R
r.stream.stats -o stream_rast=horton direction=direction elevation=elevation > tmp_file

R
# now in R
r=read.csv("tmp_file", skip=1, header=TRUE)
plot(num_of_streams~order, data=r, log="y",
     main="Sperafish area",
     sub=paste("Bifurcation ratio: ",
               round(1/10^model$coefficients[2], 3)))
model=lm(log10(num_of_streams)~order, data=r)
abline(model)
```

## REFERENCES

- Horton, R. E. (1945), *Erosional development of streams and their
    drainage basins: hydro-physical approach to quantitative
    morphology*, Geological Society of America Bulletin 56 (3): 275-370

## SEE ALSO

*[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.stream.channel](r.stream.channel.md),
[r.stream.distance](r.stream.distance.md),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.order](r.stream.order.md),
[r.stream.segment](r.stream.segment.md),
[r.stream.slope](r.stream.slope.md), [r.stream.snap](r.stream.snap.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html)*

See also [r.streams.\*
modules](https://grasswiki.osgeo.org/wiki/R.stream.*_modules) wiki page.

## AUTHOR

Jarek Jasiewicz, Adam Mickiewicz University, Geoecology and
Geoinformation Institute.
