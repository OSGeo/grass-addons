## DESCRIPTION

*r.slopeunits.create* creates a raster layer of slope units. Optionally,
a vector map can be created.

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

## REFERENCES

- Alvioli, M., Marchesini, I., Reichenbach, P., Rossi, M., Ardizzone,
  F., Fiorucci, F., and Guzzetti, F. (2016): Automatic delineation of
  geomorphological slope units with r.slopeunits v1.0 and their
  optimization for landslide susceptibility modeling, Geosci. Model
  Dev., 9, 3975-3991.
  DOI:[10.5194/gmd-9-3975-2016](https://doi.org/10.5194/gmd-9-3975-2016)
- Alvioli, M., Guzzetti, F., & Marchesini, I. (2020): Parameter-free
  delineation of slope units and terrain subdivision of Italy.
  Geomorphology, 358, 107124.
  DOI:[10.1016/j.geomorph.2020.107124](https://doi.org/10.1016/j.geomorph.2020.107124)

## SEE ALSO

*[r.slopeunits.clean](r.slopeunits.clean.md),
[r.slopeunits.metrics](r.slopeunits.metrics.md),
[r.slopeunits.optimize](r.slopeunits.optimize.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Markus Metz (refactoring), [mundialis](https://www.mundialis.de/)
