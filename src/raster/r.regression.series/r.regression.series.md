## DESCRIPTION

*r.regression.series* is a module to calculate linear regression
parameters between two time series, e.g. NDVI and precipitation.

The module makes each output cell value a function of the values
assigned to the corresponding cells in the two input raster map series.
Following methods are available:

- offset: Linear regression offset
- slope: Linear regression slope
- corcoef: Correlation Coefficent R
- rsq: Coefficient of determination = R squared
- adjrsq: Adjusted coefficient of determination
- f: F statistic
- t: T statistic

The module assumes a simple linear regression of the form

```sh
    y = a + b * x
```

*offset* is equivalent to *a* in the above equation, also referred to as
constant or intercept.

*slope* is equivalent to *b* in the above equation.

*corcoef* is the correlation coefficient R with a theoretical range of
-1,1.

*rsq* is the coefficient of determination, equivalent to the squared
correlation coefficient R<sup>2</sup>.

*adjrsq* is the coefficient of determination adjusted for the number of
samples, i.e. number of input maps per series.

*f* is the value of the F statistic.

*t* is the value of the T statistic.

## NOTES

The number of maps in *xseries* and *yseries* must be identical.

With *-n* flag, any cell for which any of the corresponding input cells
are NULL is automatically set to NULL (NULL propagation). The aggregate
function is not called, so all methods behave this way with respect to
the *-n* flag.

Without *-n* flag, the complete list of inputs for each cell (including
NULLs) is passed to the function. Individual functions can handle data
as they choose. Mostly, they just compute the parameter over the
non-NULL values, producing a NULL result only if all inputs are NULL.

Linear regression (slope, offset, coefficient of determination) requires
an equal number of *xseries* and *yseries* maps. If the different time
series have irregular time intervals, NULL raster maps can be inserted
into time series to make time intervals equal (see example).

The maximum number of raster maps to be processed is limited by the
operating system. For example, both the hard and soft limits are
typically 1024. The soft limit can be changed with e.g. `ulimit -n 1500`
(UNIX-based operating systems) but not higher than the hard limit. If it
is too low, you can as superuser add an entry in

```sh
/etc/security/limits.conf
# <domain>      <type>  <item>         <value>
your_username  hard    nofile          1500
```

This would raise the hard limit to 1500 file. Be warned that more files
open need more RAM.

## EXAMPLES

Using *r.regression.series* with wildcards:  

```sh
r.regression.series xseries="`g.list pattern='insitu_data.*' sep=,`" \
     yseries="`g.list pattern='invivo_data.*' sep=,`" \
         output=insitu_data.rsquared method=rsq
```

Note the *g.list* module also supports regular expressions for selecting
map names.

Example for multiple parameters to be computed in one run (3 resulting
parameters from 8 input maps, 4 maps per time series):

```sh
r.regression.series x=xone,xtwo,xthree,xfour y=yone,ytwo,ythree,yfour \
    out=res_offset,res_slope,res_adjrsq meth=offset,slope,adjrsq
```

## SEE ALSO

*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html),
[r.regression.line](https://grass.osgeo.org/grass-stable/manuals/r.regression.line.html),
[r.regression.multi](https://grass.osgeo.org/grass-stable/manuals/r.regression.multi.html)*

## AUTHOR

Markus Metz
