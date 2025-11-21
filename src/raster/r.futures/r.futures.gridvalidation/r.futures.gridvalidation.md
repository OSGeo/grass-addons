## DESCRIPTION

Module *r.futures.gridvalidation* allows to validate land change
simulation results on a spatial grid. It computes:

- Allocation disagreement (total and per class), see Pontius et al,
    2011
- Quantity disagreement (total and per class), see Pontius et al, 2011
- Cohen's Kappa
- Kappa simulation, see van Vliet et al, 2011

These metrics are computed for each cell of a region provided in
**region** option resulting in spatially variable validation results.
Cell size of the region should be larger than the cell size of the
current region.

This module can be used for any number of classes. Input raster
**original** represents the initial conditions and is needed only for
Kappa simulation.

## EXAMPLES

Validate FUTURES output by computing quantity and allocation
disagreement on a 5km grid. First reclassify FUTURES output to 0
(undeveloped) and 1 (developed) by creating a text file "rules.txt" with
the following content:

```text
-1 = 0
0 thru 100 = 1
```

Then save a region used as a grid:

```sh
g.region res=5000 -a save=grid
```

Reclass FUTURES output:

```sh
r.reclass input=simulated_2016 output=simulated_2016_reclass rules=rules.txt
```

Validate FUTURES output by computing kappa simulation on a 5km grid:

```sh
r.futures.gridvalidation simulated=simulated_2016_reclass reference=reference_2016 original=orig_2001 kappasimulation=kappasim
```

## SEE ALSO

[FUTURES](r.futures.md), *[r.futures.pga](r.futures.pga.md)*,
*[r.futures.potential](r.futures.potential.md)*,
*[r.futures.devpressure](r.futures.devpressure.md)*,
*[r.futures.demand](r.futures.demand.md)*,
*[r.futures.calib](r.futures.calib.md)*,
*[r.sample.category](r.sample.category.md)*

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
