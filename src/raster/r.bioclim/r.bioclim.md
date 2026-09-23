## DESCRIPTION

***r.bioclim*** calculates various bioclimatic indices from monthly
temperature and optional precipitation time series. The time series can
be averages for several years or monthly values for a specific year. In
any case all 12 months must be provided. If a precipitation time series
is not provided, only those indices based on temperature are calculated.
The names of the output maps are \<output\>bio01, \<output\>bio02,
\<output\>bio03, etc. If the suffix bioXY needs to be separated from the
**output** prefix, that separator must be part of the prefix, e.g.
*output=eurolst\_*.

If the input temperatures are scaled, e.g. as input = Celsius \* 10,
then the **inscale** option must be set to 10. Similarly, the
**outscale** option is by default 10, and temperature output is in this
case Celsius \* 10. Exceptions are BIO3, BIO4, and BIO15 which are
always multiplied by 100 (see below). The reason that **outscale** is
set to 10 by default is that the output layers are integers (for
compatibility with WORLDCLIM), and a scaling factor of 10 (or higher
power of 10) ensures a minimum of precision.

## NOTES

### Quarter years

The bioclimatic indices referring to the wettest, driest, warmest or
coldest quarter can be computed in two different ways. The default is to
divide a year into four quarters (quarters=4). Using this option the
first quarter refers to Jan - Mar, the second quarter to Apr - Jun, and
the last quarter to Oct - Dec. It is the method used to create the 250 m
[EuroLST bioclim](http://gis.cri.fmach.it/eurolst-bioclim/) data and
should be used with records for a specific year.

The second option is to divide the year in 12 quarters. With this option
the quarterly parameters are not aligned to any calendar quarters.
Instead, the first quarter refers to Jan - Mar, the second quarter to
Feb - Apr, and the last quarter to Dec - Feb. This is the same method as
used by the biovars function in the [R](https://www.r-project.org/)
package [dismo](https://cran.r-project.org/package=dismo) and how the
bioclimatic variables provided by
[Worldclim](http://worldclim.org/bioclim) were computed. This option
should be used when long-term averages are used as input.

### Precipitation data

Check the unit of measure of precipitation data. To calculate the bio18
and bio19 **r.bioclim** rounds the value of the raster to the closest
integer value. If the unit of measure of your data is, for example, kg
m-2 m-1 (i.e., fluxes per second) as in
[CHELSA](https://chelsa-climate.org/) data you will gain a raster map
with zero values for the bio18 and bio19, because the precipitation
values are very close to 0.

### List of bioclimatic indices

**BIO 01** Annual mean temperature as the mean of the monthly
temperatures (°C)

**BIO 02** Mean diurnal range as the mean of monthly (max temp - min
temp) (°C)

**BIO 03** Isothermality (BIO2/BIO7 \* 100)

**BIO 04** Temperature Seasonality (standard deviation \* 100)

**BIO 05** Max Temperature of Warmest Month (°C)

**BIO 06** Min Temperature of Coldest Month (°C)

**BIO 07** Temperature Annual Range (BIO5 - BIO6) (°C)

**BIO 08** Mean Temperature of Wettest Quarter (°C)

**BIO 09** Mean Temperature of Driest Quarter (°C)

**BIO 10** Mean Temperature of Warmest Quarter (°C)

**BIO 11** Mean Temperature of Coldest Quarter (°C)

**BIO 12** Annual Precipitation (mm)

**BIO 13** Precipitation of Wettest Month (mm)

**BIO 14** Precipitation of Driest Month (mm)

**BIO 15** Precipitation Seasonality (Coefficient of Variation \* 100)

**BIO 16** Precipitation of Wettest Quarter (mm)

**BIO 17** Precipitation of Driest Quarter (mm)

**BIO 18** Precipitation of Warmest Quarter (mm)

**BIO 19** Precipitation of Coldest Quarter (mm)

## EXAMPLES

Bioclimatic indices from worldclim data with 4 parallel processes:

```sh
r.bioclim tmin=`g.list type=rast pat=tmin_* map=. sep=,` \
          tmax=`g.list type=rast pat=tmax_* map=. sep=,` \
          prec=`g.list type=rast pat=prec_* map=. sep=,` \
          out=worldclim_ workers=4
```

## SEE ALSO

*[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*

## REFERENCES

- [Worldclim: Bioclimatic
    variables](https://www.worldclim.org/data/bioclim.html)

## AUTHOR

Markus Metz
