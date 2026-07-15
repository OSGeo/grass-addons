## DESCRIPTION

The t.rast.kappa calculate kappa parameter in a space time raster
dataset. It can calculate kappa values using two different algorithm,
the one provided by
[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html) and
the one provided by [SciKit-Learn
metrics](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)
library

## EXAMPLE

### Using r.kappa as backend

In this example t.rast.kappa is using
[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html) as
backend, it return the results inside the */tmp*em\> directory into
files with *mystrds* as prefix. *weight* option is not considered using
[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html) as
backend.

```sh
        t.rast.kappa -k strds=mystrds output=/tmp/mystrds
    
```

### Using SciKit-Learn as backend, text as output

In this example t.rast.kappa is using [SciKit-Learn
metrics](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)
library as backend, without *output* option, the module print the
results to standard output

```sh
        t.rast.kappa strds=mystrds where="start_time >= '1999-12-01' weight='linear'
    
```

### Using SciKit-Learn as backend, map as output

In this example t.rast.kappa is using [SciKit-Learn
metrics](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html)
library as backend, the output is a map with the kappa values calculated
for each pixel. The *splittingday* option is required to split the space
time raster dataset in two groups and analyze them; the two groups must
have the same number of maps, otherwise and error will be reported.

```sh
        t.rast.kappa -p strds=mystrds output=mykappa splittingday='2005-01-01'
    
```

## SEE ALSO

[r.kappa](https://grass.osgeo.org/grass-stable/manuals/r.kappa.html)

## AUTHOR

Luca Delucchi, *Fondazione Edmund Mach*
