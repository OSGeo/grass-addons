## DESCRIPTION

*r.slopeunits* is a GRASS GIS addon toolset that creates, cleans and
calculate metrics for slope units. Additionally, optimal input values
can be determined. The *r.slopeunits* toolset consists of currently four
modules:

- [r.slopeunits.create](r.slopeunits.create.md): Creates a raster layer
  of slope units. Optionally, a vector map can be created.
- [r.slopeunits.clean](r.slopeunits.clean.md): Cleans slope units layer,
  e.g. results of r.slopeunits.create.
- [r.slopeunits.metrics](r.slopeunits.metrics.md): Creates metrics for
  slope units.
- [r.slopeunits.optimize](r.slopeunits.optimize.md): Determines optimal
  input values for slope units.

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

## AUTHORS

Main authors: Ivan Marchesini, Massimiliano Alvioli, CNR-IRPI  
Markus Metz (translation to python, refactoring), Carmen Tawalika
(translation to python, refactoring),
[mundialis](https://www.mundialis.de/)
