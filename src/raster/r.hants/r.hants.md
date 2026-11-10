## DESCRIPTION

*r.hants* performs a Harmonic ANalysis of Time Series (HANTS) analysis
in order to estimate missing values and identify outliers. For each
input map, an output map with the suffix *suffix* (default: \_hants) is
created.

The option **nf**, number of frequencies, should be carefully chosen.
Different numbers of frequencies should be tested first on a small test
region before running the module on the full region. As a rule of thumb,
the number of frequencies should be at least *estimated periodicity +
3*, e.g. for NDVI with an annual cycle (one peak per year), the number
of frequencies should be at least 4 when analysing one year. If two
peaks are assumed per year, the number of frequencies should be at least
5 when analysing one year.

The number of frequencies should not be too large, either. With a large
number of frequencies, outliers can no longer be identified because the
fit is "too good", i.e. outliers can be represented by the estimates of
the curve. Moreover, the number of frequencies should be smaller than *n
input maps / 2* if missing values should be reconstructed.

## NOTES

The optional *amplitude* and *phase* output maps contain the amplitude
and phase for each frequency. The amplitude maps can be used to identify
the dominant frequency with *r.series method=max\_raster*. The baseline
frequeny (base period) has the suffix *.0*, its first harmonic has the
suffix *.1*, its second harmonic has the suffix *.2*, etc. The value of
the output of *r.series method=max\_raster* is identical to the number
of the suffix. With the *amplitude* output maps for NDVI input, this can
be used to determine the number of peaks in vegetation growth within the
base period, where 0 (zero) means that the dominant frequency is the
base period, i.e. one peak per base period.

HANTS operates in time, i.e. it looks at the time series of each cell.
To fit a harmonic curve, it requires that the time series of each cell
has a minimum amount of valid data. The number of valid observations
must always be greater than or equal to the number of parameters that
describe the harmonic curve (2 x nf - 1). The user can decide to use
more observations than this minimum required. The option **dod** (degree
of over-determination) is the minimum number of "extra" valid
observations that should be considered to fit the curve. This parameter
is optional, but it is recommended to be set.

In general, HANTS discards some information trying to represent the
input time series with a limited number of sine/cosine functions.
Therefore, most of the times, 1) it does not provide an exact match with
the input data and, 2) it produces a smoothed output. With more
frequencies, it is possible to get a better match with the input data,
but also potential overshoots. The latter can be alleviated by setting
dod \> 0 at the cost of further smoothing in the output.

The *range* parameter can be set to *low,high* thresholds: values
outside of this range are treated as NULL. The *low,high* thresholds are
floating point, so use *-inf* or *inf* for a single threshold (e.g.,
*range=0,inf* to ignore negative values, or *range=-inf,-200.4* to
ignore values above -200.4).

The length of the *base\_period* is by default the number of input maps.
If the user wants a base period of one year and the *input* or *file*
options (note that they are mutually exclusive) provides a list of maps
covering one year, then there is no need to set the base period.
Besides, if the input maps are equidistant in time, e.g. every 8 days,
there is no need to set *time\_steps*. However, if the interval is not
constant (i.e. masp are not equidistant), the user needs to assign time
steps. These must always increase (i.e. each time step must be larger
than the previous one) and the total number of time steps must be equal
to the number of input maps.

Optionally, low and/or high outliers can be removed by means of the *-l*
and *-h* flags, respectively. In this case, the parameter **fet** (fit
error tolerance) must be provided. The value of fet is relative to the
value range of the variable being considered. For further details on the
usage of the option fet, see Roerink et al. (2000).

The maximum number of raster maps that can be processed is given by the
user-specific limit of the operating system. For example, the soft
limits for users are typically 1024. The soft limit can be changed with
e.g. `ulimit -n 4096` (UNIX-based operating systems) but it cannot be
higher than the hard limit. If the latter is too low, you can as
superuser add an entry in:

```sh
/etc/security/limits.conf
# <domain>      <type>  <item>         <value>
your_username  hard    nofile          4096
```

This will raise the hard limit to 4096 files. Also have a look at the
overall limit of the operating system

```sh
cat /proc/sys/fs/file-max
```

which on modern Linux systems is several 100,000 files.

Use the **-z** flag to analyze large amounts of raster maps without
hitting open files limit and the *file* option to avoid hitting the size
limit of command line arguments. Note that the computation using the
*file* option is slower than with the *input* option. For every single
row in the output map(s) all input maps are opened and closed. The
amount of RAM will rise linearly with the number of specified input
maps. The *input* and *file* options are mutually exclusive: the former
is a comma separated list of raster map names and the latter is a text
file with a new line separated list of raster map names. Note that the
order of maps in one option or the other is very important.

## EXAMPLES

### Average temperature data example

This small example is based on a climatic dataset for North Carolina
which was from publicly available data (monthly temperature averages and
monthly precipitation sums from 2000 to 2012, downloadable as [GRASS
GIS 7
location](http://courses.ncsu.edu/mea592/common/media/02/nc_climate_spm_2000_2012.zip)):

```sh
# set computational region to one of the maps
g.region raster=2004_03_tempmean -p
```

Visualize the time series as animation:

```sh
# note: color table is different from standard "celsius"
g.gui.animation rast=`g.list type=raster pattern="*tempmean" sep=comma`
```

Since HANTS is CPU intensive, we test for now at lower resolution:

```sh
g.region -p res=5000

# HANTS: Harmonic analysis of the 156 input maps...
# just wildly guessing the parameters for a test run:

# generate and check list of input maps (the order matters!)
g.list type=raster pattern="20??_??_tempmean" output=tempmean.csv

r.hants file=tempmean.csv nf=6 dod=5 delta=0.1 base_period=12

# assign reasonable color tables for temperature
for map in `g.list type=raster pattern="*tempmean_hants"` ; do
    r.colors $map color=celsius
done

# assign degree Celsius color table
r.colors 2000_06_tempmean_hants color=celsius

# verify with one of the 156 results (still at reduced resolution):
r.mapcalc "2000_06_tempmean_diff = 2000_06_tempmean - 2000_06_tempmean_hants"

r.colors 2000_06_tempmean_diff color=differences
d.mon wx0
d.rast 2000_06_tempmean_hants
d.rast 2000_06_tempmean_diff


r.univar 2000_06_tempmean_diff -g
n=5066
null_cells=5040
cells=10106
min=-0.0899336115228095
max=0.359362050140941
range=0.449295661663751
mean=0.188579838052468
...

# see HANTS time series as animation
g.gui.animation rast=`g.list type=raster pattern="*tempmean_hants" sep=comma`


# Check HANTS behaviour in a given point
east=740830
north=168832

for map in `g.list rast pat="20??_??_tempmean"` ; do
  r.what map=$map coordinates=$east,$north >> time_series_orig.csv
done

for map in `g.list rast pat="*tempmean_hants"` ; do
  r.what map=$map coordinates=$east,$north >> time_series_hants.csv
done

# merge files:
echo "east|north|temp_orig|temp_hants" > time_series_final.csv

paste -d'|' time_series_orig.csv time_series_hants.csv | \
      cut -d'|' -f1,2,4,8 >> time_series_final.csv

# Resulting CSV file: 'time_series_final.csv'
```

### Using t.\* modules to check for basic statistics

The temporal framework (t.\* modules) can be used to assess basic
statistics:

```sh
# create spatio temporal data set with hants output maps
t.create type=strds temporaltype=absolute  output=tempmean_hants \
  title="Mean Temperature HANTS" description="Mean Temperature reconstructed with HANTS"

# register maps in the strds
t.register -i type=raster input=tempmean_hants \
  maps=`g.list raster pattern=*tempmean_hants sep=,` start="2000-01-01" \
  increment="1 months"

# getting general info of the strds (including max and min of the whole series)
t.info type=strds input=tempmean_hants

# getting statistics for each map in the series
t.rast.univar -h tempmean_hants > stats_hants.txt
```

## SEE ALSO

*[r.series](https://grass.osgeo.org/grass-stable/manuals/r.series.html)*
*[r.series.lwr](r.series.lwr.md)*

## REFERENCES

Roerink, G. J., Menenti, M. and Verhoef, W., 2000. Reconstructing
cloudfree NDVI composites using Fourier analysis of time series.
International Journal of Remote Sensing, 21 (9), 1911-1917. DOI:
[10.1080/014311600209814](https://doi.org/10.1080/014311600209814)

## AUTHOR

Markus Metz
