## DESCRIPTION

*r.mregression.series* is a module to calculate multiple linear
regression parameters between several time series, e.g. NDVI and
elevation, precipitation. It s a front-end for models from
*python-statmodels* package.

The module makes each output cell value a function of the values
assigned to the corresponding cells in the input raster map series.

The module assumes a simple linear regression of the form

```sh
    Y(t) = b1 * X1(t) + b2 * X2(t) + ... + bn * Xn(t)
```

The module uses two models: ordinary least squares and robust linear
models.

## NOTES

The module performs multiple linear regression, use
[r.regression.series](r.regression.series.md) for regression with one
predictor.

The number of predictor variables (*X* maps) must be the same in each
(time) series (see examples below). If the different predictors have
different or irregular time intervals, NULL raster maps can be inserted
into time series to make time intervals equal.

The list of raster inputs (including NULLs) is passed to the regression
function. The function computes the parameters over the non-NULL values,
producing a NULL result only if there aren't enough non-NULL values for
computing.

## EXAMPLES

The most important paramether is *samples*; it provides the list of *Y*
and *X* maps. The parameter is the name of csv file of the next
structure: the first line is a header, other lines provide names of the
*Y* and *X* maps. The header contains the names of the input and output
variables.

For example the csv file for regression between NDVI and (elevation,
precipitation)

```sh
    NDVI = b1*Elevation + b2*Precipitation
```

could be the next file:

```sh
y,elevation,precipipation
ndvi_1,elev_1,precip_1
ndvi_2,elev_2,precip_2
...
ndvi_n,elev_n,precip_n
```

"ndvi\_t" are names of the NDVI rasters, "precip\_t" are names of
precipitation rasters. The names of the first and the second predictor
variables are "elevation" and "precipitation" accordingly.

The second paramether is *result\_prefix*. It is used for construction
of the coefficient names. For example if result\_prefix="coef.", the
names of the regression coefficients will be "coef.elevation" and
"coef.precipitation".

```sh
r.mregression.series samples=settings result_prefix="coef."
```

If the regression model includes the intercept

```sh
    NDVI = b0 + b1*Elevation + b2*Precipitation
```

then the constant map should be used:

```sh
r.mapcalc "ones = 1.0"
```

and the csv file is:

```sh
y,offset,elevation,precipipation
ndvi_1,ones,elev_1,precip_1
ndvi_2,ones,elev_2,precip_2
...
ndvi_n,ones,elev_n,precip_n
```

Then the command

```sh
r.mregression.series samples=settings result_prefix="coef."
```

produces three raster maps: "coef.offset", "coef.elevation",
"coef.precipitation".

### EXAMPLE 1

Create test data for the example. Suppose we have five *Y* maps and 5
pairs of predictor *X* = *(x1, x2)* maps.

Create *X* variables (random numbers):

```sh
r.mapcalc -s "x11 = rand(0, 20)"
r.mapcalc -s "x21 = rand(0, 20)"
r.mapcalc -s "x31 = rand(0, 20)"
r.mapcalc -s "x41 = rand(0, 20)"
r.mapcalc -s "x51 = rand(0, 20)"
```

```sh
r.mapcalc -s "x12 = rand(0, 20)"
r.mapcalc -s "x22 = rand(0, 20)"
r.mapcalc -s "x32 = rand(0, 20)"
r.mapcalc -s "x42 = rand(0, 20)"
r.mapcalc -s "x52 = rand(0, 20)"
```

Create constant raster for the intercept:

```sh
r.mapcalc  "ones = 1.0"
```

Suppose *Y* is a linear function of *x1* and *x2* variables plus a
random error. (For testing purposes we assume that *Y* = *12 + 5\*x1 +
3\*x2*). Create 5 Y rasters:

```sh
r.mapcalc -s "y1 = 12 + 5* x11 + 3*x12 + rand(0, 4)"
r.mapcalc -s "y2 = 12 + 5* x21 + 3*x22 + rand(0, 4)"
r.mapcalc -s "y3 = 12 + 5* x31 + 3*x32 + rand(0, 4)"
r.mapcalc -s "y4 = 12 + 5* x41 + 3*x42 + rand(0, 4)"
r.mapcalc -s "y5 = 12 + 5* x51 + 3*x52 + rand(0, 4)"
```

So we have five test rasters *Y* and *X*. Forget for a moment that we
know the function and try to find the coeffitients.

Create *samples* csv file:

```sh
echo "y,bias,x1,x2
y1,ones,x11,x12
y2,ones,x21,x22
y3,ones,x31,x32
y4,ones,x41,x42
y5,ones,x51,x52" > settings.csv
```

Run the command

```sh
r.mregression.series samples=settings.csv result_prefix="coef."
```

Three raster maps will be created: "coef.bias", "coef.x1", "coef.x2".
This rasters contains the fitted coefitients.

## SEE ALSO

*[r.regression.series](r.regression.series.md),
[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html),
[r.regression.line](https://grass.osgeo.org/grass-stable/manuals/r.regression.line.html),
[g.list](https://grass.osgeo.org/grass-stable/manuals/g.list.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*

## AUTHOR

Dmitry Kolesov
