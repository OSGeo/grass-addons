## DESCRIPTION

*r.slopeunits.clean* cleans slope units layer, e.g. results of
*r.slopeunits.create*.

## NOTES

## EXAMPLE

```sh
r.slopeunits.clean \
    demmap=dem_italia_isolegrandi@su_test \
    plainsmap=flat \
    slumap=su_tmp \
    slumapclean=su_tmp_cl \
    cleansize=25000 \
    -m
```

## SEE ALSO

*[r.slopeunits.create](r.slopeunits.create.md),
[r.slopeunits.metrics](r.slopeunits.metrics.md),
[r.slopeunits.optimize](r.slopeunits.optimize.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Markus Metz (refactoring, translation of "clean\_method\_3" to python),
Carmen Tawalika (creation of extra addon),
[mundialis](https://www.mundialis.de/)
