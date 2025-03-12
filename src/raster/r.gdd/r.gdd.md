## DESCRIPTION

*r.gdd* calculates (accumulated) growing degree days
([GDDs](https://en.wikipedia.org/wiki/Growing_degree-day)), [Winkler
indices](https://en.wikipedia.org/wiki/Winkler_index), Biologically
Effective Degree Days (BEDD), and Huglin indices from several input maps
with temperature data for different times of the day.

**GDDs** are calculated as

```text
    gdd = average - baseline
```

The **Winkler index** is calculated as

```text
    wi = average - baseline
```

usually accumulated for the period April 1<sup>st</sup> to October
31<sup>st</sup> (northern hemisphere) or the period October
1<sup>st</sup> to April 30<sup>th</sup> (southern hemisphere).

**BEDDs** are calculated as

```text
    bedd = average - baseline
```

with an optional upper *cutoff* applied to the average. Vine development
kinetics for example reach a plateau at an average daily temperature of
19°C.

The **Huglin heliothermal index** is calculated as

```text
    hi = (average + max) / 2 - baseline
```

usually accumulated for the period April 1<sup>st</sup> to September
30<sup>th</sup> (northern hemisphere) or the period September
1<sup>st</sup> to April 30<sup>th</sup> (southern hemisphere).

Any averages above the *cutoff* value are set to *cutoff*, and any
*average* values below the *baseline* value are set to *baseline*.
Negative results are set to 0 (zero).

The *shift* and *scale* values are applied directly to the input values.
The *baseline*, *cutoff*, and *range* options are applied to the shifted
and scaled values.

If an existing map is provided with the *add* option, the values of this
map are added to the output, thus accumulating the selected index.

## NOTES

The *scale* and *shift* parameters are used to transform input values
with

```text
    new = old * scale + shift
```

With the *-n* flag, any cell for which any of the corresponding input
cells are NULL is automatically set to NULL (NULL propagation) and the
index is not calculated.

Without the *-n* flag, all non-NULL cells are used to calculate the
selected index.

If the *range=* option is given, any values which fall outside that
range will be treated as if they were NULL. Note that the range is
applied to the scaled and shifted input data. The *range* parameter can
be set to *low,high* thresholds: values outside of this range are
treated as NULL (i.e., they will be ignored by most aggregates, or will
cause the result to be NULL if -n is given). The *low,high* thresholds
are floating point, so use *-inf* or *inf* for a single threshold (e.g.,
*range=0,inf* to ignore negative values, or *range=-inf,-200.4* to
ignore values above -200.4).

The number of raster maps to be processed is given by the limit of the
operating system. For example, both the hard and soft limits are
typically 1024. The soft limit can be changed with e.g. `ulimit -n 1500`
(UNIX-based operating systems) but not higher than the hard limit. If it
is too low, you can as superuser add an entry in

```text
/etc/security/limits.conf
# <domain>      <type>  <item>         <value>
your_username  hard    nofile          1500
```

This would raise the hard limit to 1500 file. Be warned that more files
open need more RAM.

Use the *file* option to analyze large amount of raster maps without
hitting open files limit and the size limit of command line arguments.
The computation is slower than the *input* option method. For every
sinlge row in the output map(s) all input maps are opened and closed.
The amount of RAM will rise linear with the number of specified input
maps. The input and file options are mutually exclusive. Input is a text
file with a new line separated list of raster map names.

## EXAMPLES

Example with MODIS Land Surface Temperature, transforming values from
Kelvin \* 50 to degrees Celsius:

```sh
r.gdd in=MOD11A1.Day,MOD11A1.Night,MYD11A1.Day,MYD11A1.Night out=MCD11A1.GDD \
      scale=0.02 shift=-273.15 baseline=10 cutoff=30
```

## SEE ALSO

*[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html),
[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*

## AUTHOR

Markus Metz (based on r.series)
