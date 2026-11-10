## DESCRIPTION

*r.gwr* calculates a geographically weighted multiple linear regression
from raster maps, according to the formula

```text
Y = b0 + sum(bi*Xi) + E
```

where

```text
X = {X1, X2, ..., Xm}
m = number of explaining variables
Y = {y1, y2, ..., yn}
Xi = {xi1, xi2, ..., xin}
E = {e1, e2, ..., en}
n = number of observations (cases)
```

In R notation:

```R
Y ~ sum(bi*Xi)
b0 is the intercept, X0 is set to 1
```

The β coefficients are localized, i.e. determined for each cell
individually. These β coefficients are the most important output of
*r.gwr*. Spatial patterns and localized outliers in these coefficients
can reveal details of the relation of Y to X. Outliers in the β
coefficients can also be caused by a small bandwidth and can be removed
by increasing the bandwidth.

Geographically weighted regressions should be used as a diagnostic tool
and not as an interpolation method. If a geographically weighted
regression provides a higher R squared than the corresponding global
regression, then a crucial predictor is missing in the model. If that
missing predictor can not be estimated or is supposed to behave
randomly, a geographically weighted regression might be used for
interpolation, but the result, in particular the variation of the β
coefficients needs to be judged according to prior assumptions. See also
the manual and the examples of the R package
[spgwr](http://cran.rstudio.com/web/packages/spgwr/index.html).

*r.gwr* is designed for large datasets that can not be processed in R. A
p value is therefore not provided, because even very small, meaningless
effects will become significant with a large number of cells. Instead it
is recommended to judge by the amount of variance explained (R squared
for a given variable) and the gain in AIC (AIC without a given variable
minus AIC global must be positive) whether the inclusion of a given
explaining variable in the model is justified.

### The explaining variables

R squared for each explaining variable represents the additional amount
of explained variance when including this variable compared to when
excluding this variable, that is, this amount of variance is explained
by the current explaining variable after taking into consideration all
the other explaining variables.

The F score for each explaining variable allows to test if the inclusion
of this variable significantly increases the explaining power of the
model, relative to the global model excluding this explaining variable.
That means that the F value for a given explaining variable is only
identical to the F value of the R-function *summary.aov* if the given
explaining variable is the last variable in the R-formula. While R
successively includes one variable after another in the order specified
by the formula and at each step calculates the F value expressing the
gain by including the current variable in addition to the previous
variables, *r.gwr* calculates the F-value expressing the gain by
including the current variable in addition to all other variables, not
only the previous variables.

### Bandwidth

The bandwidth is the crucial parameter for geographically weighed
regressions. A too small bandwidth will essentially use the weighed
average, any predictors are mostly ignored. A too large bandwidth will
produce results similar to a global regression, and spatial
non-stationarity can not be explored.

### Adaptive bandwidth

Instead of using a fixed bandwidth (search radius for each cell), an
adaptive bandwidth can be used by specifying the number of points to be
used for each local regression with the *npoints* option. The module
will find the nearest *npoints* points for each cell, adapt the bandwith
accordingly and then calculate a local weighted regression.

### Kernel functions

The kernel function has little influence on the result, much more
important is the bandwidth. Available kernel funtions to calculate
weights are

- **Epanechnikov**  
    w = 1 - d / bw
- **Bisquare (Quartic)**  
    w = (1 - (d / bw)<sup>2</sup>)<sup>2</sup>
- **Tricubic**  
    w = (1 - (d / bw)<sup>3</sup>)<sup>3</sup>
- **Gaussian**  
    w = exp(-0.5 \* (d / bw)<sup>2</sup>)

with  
w = weight for current cell  
d = distance to the current cell  
bw = bandwidth

### Masking

A *mask* map can be provided (e.g. with **r.mask**) to restrict LWR to
those cells where the mask map is not NULL and not 0 (zero).

## REFERENCES

Brunsdon, C., Fotheringham, A.S., and Charlton, M.E., 1996,
Geographically Weighted Regression: A Method for Exploring Spatial
Nonstationarity, Geographical Analysis, 28(4), 281- 298  
Fotheringham, A.S., Brunsdon, C., and Charlton, M.E., 2002,
Geographically Weighted Regression: The Analysis of Spatially Varying
Relationships, Chichester: Wiley.  

## SEE ALSO

<https://geoinformatics.wp.st-andrews.ac.uk/gwr/>  
<http://gwr.nuim.ie/>  
R package [spgwr](https://cran.r-project.org/package=spgwr)

## AUTHOR

Markus Metz
