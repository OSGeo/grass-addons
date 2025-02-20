## DESCRIPTION

*r.slopeunits.create* creates a raster layer of slope units. Optionally,
a vector map can be created.

## NOTES

## EXAMPLE

```sh
r.slopeunits.create \
    demmap=dem_italia_isolegrandi@su_test \
    plainsmap=flat \
    slumap=su_tmp \
    thresh=250000 \
    areamin=200000 \
    cvmin=0.25 \
    rf=2 \
    maxiteration=50
```

## SEE ALSO

*[r.slopeunits.clean](r.slopeunits.clean.md),
[r.slopeunits.metrics](r.slopeunits.metrics.md),
[r.slopeunits.optimize](r.slopeunits.optimize.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Markus Metz (refactoring), [mundialis](https://www.mundialis.de/)
