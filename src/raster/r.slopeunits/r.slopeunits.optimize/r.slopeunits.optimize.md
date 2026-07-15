## DESCRIPTION

*r.slopeunits.optimize* determines optimal input values for slope units:

- "areamin" - Minimum area (m^2) below which the slope unit is not
  further segmented
- "cvmin" - Minimum value of the circular variance (0.0-1.0) below which
  the slope unit is not further segmented

It calls *r.slopeunits.create*, *r.slopeunits.clean*, and
*r.slopeunits.metrics* iteratively. Output is a file `opt.txt` with
optimal values in either specified folder or in folder `output/`" in the
current working directory. Also files `calcd.dat` and `current.txt` are
created with all determined and examined values and the four latest
examined values (combination of
`areamin`` and ``cvmin`` minimum and maximum) and ``center``, respectively.`

## EXAMPLE

```sh
r.slopeunits.optimize \
    basin=basin_chk \
    demmap=dem_italia_isolegrandi@su_test \
    plainsmap=flat \
    thresh=250000 \
    rf=2 \
    maxiteration=50 \
    cleansize=25000
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
[r.slopeunits.metrics](r.slopeunits.metrics.md)*

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Carmen Tawalika (translation to python, refactoring),
[mundialis](https://www.mundialis.de/)
