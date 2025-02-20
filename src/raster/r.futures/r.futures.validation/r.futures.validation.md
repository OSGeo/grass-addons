## DESCRIPTION

Module *r.futures.validation* allows to validate land change simulation
results. It computes:

  - Allocation disagreement (total and per class), see Pontius et al,
    2011
  - Quantity disagreement (total and per class), see Pontius et al, 2011
  - Cohen's Kappa
  - Kappa simulation, see van Vliet et al, 2011

This module can be used for any number of classes. Input raster
**original** represents the initial conditions and is needed only for
Kappa simulation.

## EXAMPLES

Validate land change simulation output by computing quantity and
allocation disagreement.

```sh
r.reclass input=simulated_2016 output=simulated_2016_reclass rules=rules.txt
r.futures.validation simulated=simulated_2016_reclass reference=reference_2016 original=orig_2001
```

## SEE ALSO

For alternative validation metrics see
[r.confusionmatrix](r.confusionmatrix.md), [r.kappa](r.kappa.md)

## REFERENCES

  - Robert Gilmore Pontius Jr & Marco Millones (2011). [Death to Kappa:
    birth of quantity disagreement and allocation disagreement for
    accuracy assessment](https://doi.org/10.1080/01431161.2011.552923).
    International Journal of Remote Sensing, 32:15, 4407-4429
  - Jasper van Vliet, Arnold K. Bregt, Alex Hagen-Zanker (2011)
    [Revisiting Kappa to account for change in the accuracy assessment
    of land-use change
    models](https://doi.org/10.1016/j.ecolmodel.2011.01.017). Ecological
    Modelling, Volume 222, Issue 8.
  - Meentemeyer, R. K., Tang, W., Dorning, M. A., Vogler, J. B.,
    Cunniffe, N. J., & Shoemaker, D. A. (2013). [FUTURES: Multilevel
    Simulations of Emerging Urban-Rural Landscape Structure Using a
    Stochastic Patch-Growing
    Algorithm](https://doi.org/10.1080/00045608.2012.707591). Annals of
    the Association of American Geographers, 103(4), 785-807. DOI:
    10.1080/00045608.2012.707591
  - Dorning, M. A., Koch, J., Shoemaker, D. A., & Meentemeyer, R. K.
    (2015). [Simulating urbanization scenarios reveals tradeoffs between
    conservation planning
    strategies](https://doi.org/10.1016/j.landurbplan.2014.11.011).
    Landscape and Urban Planning, 136, 28-39. DOI:
    10.1016/j.landurbplan.2014.11.011
  - Petrasova, A., Petras, V., Van Berkel, D., Harmon, B. A., Mitasova,
    H., & Meentemeyer, R. K. (2016). [Open Source Approach to Urban
    Growth
    Simulation](https://isprs-archives.copernicus.org/articles/XLI-B7/953/2016/isprs-archives-XLI-B7-953-2016.pdf).
    Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci., XLI-B7,
    953-959. DOI: 10.5194/isprsarchives-XLI-B7-953-2016

## AUTHOR

Anna Petrasova, [NCSU
GeoForAll](https://geospatial.ncsu.edu/geoforall/)
