## DESCRIPTION

*r.series.decompose* is a module to calculate decomposintion of signal
X.

```text
X(t) = B0 + B1*t + B2*sin(B1*t) + B3 * cos(B1*t) + ... + B{n-1}*sin(Bk*t) + Bn * cos(Bk*t) + e
```

where *X* is a raster time series, *t* is time (*t* in *\[0, pi\]*),
*sin(Fi\*t)* and *cos(Fi\*t)* are time variables; *Fi* are user specifed
frequencies; *e* is a error.

The module used r.mregression.series to find the regression coefficients
*Bi*, then it produces the fitted rasters series *X(t)* using the
coefficients.

So the module makes each output cell value a function of the values
assigned to the corresponding cells in the time variable raster map
series and the rasters of the coefficients.

*input* Raster names of equally spaced time series *X*

*result\_prefix* Prefix for raster names of filterd *X(t)*

*coef\_prefix* Prefix for names of result raster (rasters of
coefficients)

*timevar\_prefix* Prefix for names of result raster (rasters of time
variables)

*freq* List of frequencies for sin and cos functions

## NOTES

*X* must be equally spaced time serie. If the serie isn't equally
spaced, insert NULL raster maps into *X*.

The list of inputs for each cell (including NULLs) is passed to the
regression function. The functin compute the parameters over the
non-NULL values, producing a NULL result only if there aren't enough
non-NULL values for computing. The regression coefficients *Bi* are
stored in raster maps. They can be used for construct more detail time
series via the equation:

```text
X(t) = B0 + B1*t + B2*sin(B1*t) + B3 * cos(B1*t) + ... + B{n-1}*sin(Bk*t) + Bn * cos(Bk*t) + e
```

To do that the user have to create time variables (*t*, *sin(Fi\*t)* and
*cos(Fi\*t)*) at desired time *T0* and then use r.mapcalc to produce the
*X(T0)*.

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

Suppose we have time series of MODIS NDVI data (from 01 jan to 27 dec):

```sh
> g.mlist rast pattern="mod*", separator=','
mod2003_01_01,mod2003_01_09,...,mod2003_12_27
```

We use one year data, so we suppose the there is a half of sinusoid
signal in the data (NDVI values icrease, then decrease usualy). So 01
jan is t0==0, 27 dec is tn==2\*pi, there is a frequence 0.5 in the data
(and there are more frequencies, for example 1.0 and 1.5).

Decompose the signal:

```sh
> maps = $(g.list rast pattern="mod*", separator=',')
> r.series.decompose input=$maps coef_prefix="coef." \
    timevar_prefix="dec." result_pref="res." \
    freq=0.5,1.0,1.5
```

The command creates rasters of the coefficiens *coef.\**:

```text
coef.const
coef.time
coef.sin_fr0.5
coef.cos_fr0.5
coef.sin_fr1.0
coef.cos_fr1.0
coef.cos_fr1.5
coef.sin_fr1.5
```

and rasters of fitted NDVI *res.\**:

```text
res.mod2003_01_01
res.mod2003_01_09
...
```

To compute NDVI for 03 jan we need: (1) find time *T* for 03 jan (2)
create time variables for 02 jan.

The length (in days) of the NDVI time series is 362, 03 jan is the third
day of the series, so *T* = *3 \* (2\*pi/362)* radians. But r.mapcalc
uses degrees for *sin()* and *cos()* functions. So *T* = *3 \* 360/362*
degrees.

Create time variables:

```sh
r.mapcalc "T = 3.0 * 360.0/362.0"
r.mapcalc "sin0.5 = sin(0.5*3.0*360.0/362.0)"
r.mapcalc "cos0.5 = cos(0.5*3.0*360.0/362.0)"
r.mapcalc "sin1 = sin(3.0*360.0/362.0)"
r.mapcalc "cos1 = cos(3.0*360.0/362.0)"
r.mapcalc "sin1.5 = sin(1.5*3.0*360.0/362.0)"
r.mapcalc "cos1.5 = cos(1.5*3.0*360.0/362.0)"
```

Create NDVI for 03 jan:

```sh
r.mapcals "ndvi03jan = coef.const + coef.time*T +\
    coef.sin_fr0.5*sin0.4 + coef.cos_fr0.5*cos0.5 +\
    coef.sin_fr1.0*sin1 + coef.cos_fr1.0*cos1 +\
    coef.sin_fr1.5*sin1.5 + coef.cos_fr1.5*cos1.5"
```

## SEE ALSO

*[r.regression.series](addons/r.mregression.series.md)*,
*[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html)*,
*[r.regression.line](https://grass.osgeo.org/grass-stable/manuals/r.regression.line.html)*,
*[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html)*,

## AUTHOR

Dmitry Kolesov
