## DESCRIPTION

*v.krige* allows performing Kriging operations in GRASS GIS environment,
using R software functions in background.

## NOTES

*v.krige* is just a front-end to R. The options and parameters are the
same offered by packages *automap* and *gstat*.

Kriging, like other interpolation methods, is fully dependent on input
data features. Exploratory analysis of data is encouraged to find out
outliers, trends, anisotropies, uneven distributions and consequently
choose the kriging algorithm that will give the most acceptable result.
Good knowledge of the dataset is more valuable than hundreds of
parameters or powerful hardware. See Isaaks and Srivastava's book,
exhaustive and clear even if a bit outdated.

Auto-fit variogram option will update partial sill, nugget, range and
kappa values with fitted ones. Enabling the values will pass them to
auto-fit and thus preserve from modification and thus they might differ
from fitted ones. Sill value can be tetermined by summing partial sill
with nugget.

### Dependencies

- **R software \>= 2.x**

- **rpy2**  
    Python binding to R. Note\! `rpy` version 1 is not supported.

- **R packages automap, gstat, rgrass7 and rgeos.**  
    automap is optional (provides automatic variogram fit).

Install Rpy2 via pip(3):

```sh
sudo pip3 install Rpy2
```

Install the following packages via R command line (or your preferred
GUI):

```R
  install.packages("rgeos", dep=T)
  install.packages("rgdal", dep=T)
  install.packages("gstat", dep=T)
  install.packages("rgrass7", dep=T)
  install.packages("automap", dep=T)
```

#### Notes for Debian GNU/Linux

Install the dependiencies. **Attention\! python-rpy IS NOT SUITABLE.**
(compare also installation via pip above):

```sh
  aptitude install R python-rpy2
```

To install R packages, use either R's functions listed above (as root or
as user), either the Debian packages \[5\], add to repositories' list
for 32bit or 64bit (pick up the suitable line):

```sh
  deb http://debian.cran.r-project.org/cran2deb/debian-i386 testing/
  deb http://debian.cran.r-project.org/cran2deb/debian-amd64 testing/
```

and get the packages via aptitude:

```sh
  aptitude install r-cran-gstat r-cran-rgrass7
```

#### Notes for Windows

Compile GRASS GIS following this
[guide](https://trac.osgeo.org/grass/wiki/CompileOnWindows). You could
also use Linux in a virtual machine. Or install Linux in a separate
partition of the HD. This is not as painful as it appears, there are
lots of guides over the Internet to help you.

### Computation time issues

Please note that although high number of input data points and/or high
region resolution contribute to a better output, both will also slow
down the kriging calculation.

## EXAMPLES

Kriging example based on elevation map ([North Carolina sample data
set](https://grass.osgeo.org/download/data/)).

**Part 1: random sampling** of 2000 vector points from known elevation
map. Each point will receive the elevation value from the elevation
raster, as if it came from a point survey.

```sh
# reduce resolution for this example
g.region raster=elevation -p res=100
v.random output=rand2k_elev npoints=2000
v.db.addtable map=rand2k_elev columns="elevation double precision"
v.what.rast map=rand2k_elev raster=elevation column=elevation
```

**Part 2: remove points lacking elevation attributes**. Points sampled
at the border of the elevation map didn't receive any value. v.krige has
no preferred action to cope with no data values, so the user must check
for them and decide what to do (remove points, fill with the value of
the nearest point, fill with the global/local mean...). In the following
line of code, points with no data are removed from the map.

```sh
v.extract input=rand2k_elev output=rand2k_elev_filt where="elevation not NULL"
```

Check the result of previous line ("number of NULL attributes" must be
0):

```sh
v.univar map=rand2k_elev_filt type=point column=elevation
```

**Part 3: reconstruct DEM through kriging**. The simplest way to run
*v.krige* from CLI is using automatic variogram fit (note: requires R's
automap package). Output map name is optional, the modules creates it
automatically appending "\_kriging" to the input map name and also
checks for overwrite. If output\_var is specified, the variance map is
also created. Automatic variogram fit is provided by R package automap.
The variogram models tested by the fitting functions are: exponential,
spherical, Gaussian, Matern, M.Stein's parametrisation. A wider range of
models is available from gstat package and can be tested on the GUI via
the variogram plotting. If a model is specified in the CLI, also partial
sill, nugget and range values are to be provided, otherwise an error is
raised (see second example of *v.krige* command).

```sh
# automatic variogram fit
v.krige input=rand2k_elev_filt column=elevation \
        output=rand2k_elev_kriging output_var=rand2k_elev_kriging_var

# define variogram model, create variance map as well
v.krige input=rand2k_elev_filt column=elevation \
        output=rand2k_elev_filt_kriging output_var=rand2k_elev_filt_kriging_var \
        model=Mat psill=2500 nugget=0 range=1000
```

Or run wxGUI, to interactively fit the variogram and explore options:

```sh
v.krige
```

**Calculate prediction error**:

```sh
r.mapcalc "rand2k_elev_kriging_pe = sqrt(rand2k_elev_kriging_var)"
r.univar map=elevation
r.univar map=rand2k_elev_kriging
r.univar map=rand2k_elev_kriging_pe
```

The results show high errors, as the kriging techniques (ordinary and
block kriging) are unable to handle a dataset with a trend, like the one
used in this example: elevation is higher in the southwest corner and
lower on northeast corner. Universal kriging can give far better results
in these cases as it can handle the trend. It is available in R package
gstat and will be part in a future v.krige release.

## SEE ALSO

R package [gstat](https://cran.r-project.org/package=gstat), maintained
by Edzer J. Pebesma and others

R package [rgrass7](https://cran.r-project.org/package=rgrass7),
maintained by Roger Bivand

The [Short Introduction to Geostatistical and Spatial Data Analysis with
GRASS GIS and R statistical data
language](https://grasswiki.osgeo.org/wiki/R_statistics) at the GRASS
Wiki (includes installation tips). It contains a subsection about
**rgrass7**.

v.krige's [wiki
page](https://grasswiki.osgeo.org/wiki/V.krige_GSoC_2009)

Overview: [Interpolation and
Resampling](https://grasswiki.osgeo.org/wiki/Interpolation) in GRASS GIS

## REFERENCES

Isaaks and Srivastava, 1989: "An Introduction to Applied Geostatistics"
(ISBN 0-19-505013-4)

## AUTHOR

Anne Ghisla, Google Summer of Code 2009
