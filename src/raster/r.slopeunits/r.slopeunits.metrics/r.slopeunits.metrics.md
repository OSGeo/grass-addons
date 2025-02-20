## DESCRIPTION

*r.slopeunits.metrics* creates metrics for slope units. Returns output
"areamin, cvmin, v\_fin and i\_fin" to stdout, optionally writes to a
file.

## NOTES

## EXAMPLE

```sh
r.slopeunits.metrics \
    basin=basin_chk \
    demmap=dem_italia_isolegrandi@su_test \
    slumapclean=su_tmp_cl \
    cleansize=25000 \
    areamin=50000.0 \
    cvmin=0.05 \
    resolution=625 \
    outfile=objf_1.dat
```

## SEE ALSO

*[r.slopeunits.create](r.slopeunits.create.md),
[r.slopeunits.clean](r.slopeunits.clean.md),
[r.slopeunits.optimize](r.slopeunits.optimize.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Carmen Tawalika (translation to python),
[mundialis](https://www.mundialis.de/)
