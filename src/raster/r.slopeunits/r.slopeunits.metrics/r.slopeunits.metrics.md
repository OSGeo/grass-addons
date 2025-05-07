## DESCRIPTION

*r.slopeunits.metrics* creates metrics for slope units. Returns output
"areamin, cvmin, v_fin and i_fin" to stdout, optionally writes to a
file.

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

*[r.slopeunits.create](r.slopeunits.create.md),
[r.slopeunits.clean](r.slopeunits.clean.md),
[r.slopeunits.optimize](r.slopeunits.optimize.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Carmen Tawalika (translation to python),
[mundialis](https://www.mundialis.de/)
