## DESCRIPTION

Tool *r.futures.validation* allows to
validate land change simulation results.
It computes:

- Allocation disagreement (total and per class), see Pontius et al, 2011
- Quantity disagreement (total and per class), see Pontius et al, 2011
- Cohen's Kappa
- Kappa simulation, see van Vliet et al, 2011

This tool can be used for any number of classes.
Input raster **original** represents the initial conditions
and is needed for Kappa simulation and for change detection metrics.

When **original** is provided and the input rasters contain
only binary categories (0 for undeveloped and 1 for developed),
the tool additionally computes change detection metrics:

- Hits: observed change correctly simulated as change
- Misses: observed change incorrectly simulated as persistence
- False alarms: observed persistence incorrectly simulated as change
- Null successes: observed persistence correctly simulated as persistence
- Figure of merit: hits / (hits + misses + false alarms)
- Producer's accuracy: hits / (hits + misses)
- User's accuracy: hits / (hits + false alarms)

These metrics are reported as proportions of the total number of cells.
Cells already developed in the **original** raster are excluded
from the change analysis and reported separately as initially developed.
When more than two categories are present, these metrics are skipped.

## EXAMPLES

Validate land change simulation output by computing quantity and allocation
disagreement, kappa statistics, and change detection metrics.

First, reclassify the FUTURES simulation output
(where -1 is undeveloped, 0 is initially developed,
and 1 to N is the step when a cell became developed)
to binary (0 = undeveloped, 1 = developed).
Create a file `reclass_rules.txt` with the following content:

```text
-1 = 0 undeveloped
0 thru 1000 = 1 developed
```

Then reclassify and run the validation:

```sh
r.reclass input=simulated_2016 output=simulated_2016_reclass rules=reclass_rules.txt
r.futures.validation simulated=simulated_2016_reclass reference=reference_2016 \
    original=orig_2001 format=json
```

Example output:

```json
{
    "quantity_class_0": 0.015,
    "quantity_class_1": 0.015,
    "allocation_class_0": 0.023,
    "allocation_class_1": 0.023,
    "total_quantity": 0.015,
    "total_allocation": 0.023,
    "kappa": 0.852,
    "kappasimulation": 0.15,
    "misses": 0.032,
    "hits": 0.04,
    "false_alarms": 0.021,
    "null_successes": 0.507,
    "figure_of_merit": 0.4301,
    "producer": 0.5556,
    "user": 0.6557,
    "initially_developed": 0.4
}
```

## REFERENCES

Validation references:

- Robert Gilmore Pontius Jr & Marco Millones (2011).
  [Death to Kappa: birth of quantity disagreement and allocation disagreement for accuracy
  assessment](https://doi.org/10.1080/01431161.2011.552923).
  International Journal of Remote Sensing, 32:15, 4407-4429
- Jasper van Vliet, Arnold K. Bregt, Alex Hagen-Zanker (2011)
  [Revisiting Kappa to account for change in the accuracy assessment of land-use change
  models](https://doi.org/10.1016/j.ecolmodel.2011.01.017).
  Ecological Modelling, Volume 222, Issue 8.

FUTURES references:

- Meentemeyer, R. K., Tang, W., Dorning, M. A., Vogler, J. B.,
  Cunniffe, N. J., & Shoemaker, D. A. (2013). *FUTURES: Multilevel
  Simulations of Emerging Urban-Rural Landscape Structure Using a
  Stochastic Patch-Growing Algorithm*. Annals of
  the Association of American Geographers, 103(4), 785-807. DOI:
  [10.1080/00045608.2012.707591](https://doi.org/10.1080/00045608.2012.707591)
- Dorning, M. A., Koch, J., Shoemaker, D. A., & Meentemeyer, R. K.
  (2015). *Simulating urbanization scenarios reveals tradeoffs between
  conservation planning strategies*.
  Landscape and Urban Planning, 136, 28-39. DOI:
  [10.1016/j.landurbplan.2014.11.011](https://doi.org/10.1016/j.landurbplan.2014.11.011)
- Petrasova, A., Petras, V., Van Berkel, D., Harmon, B. A., Mitasova,
  H., & Meentemeyer, R. K. (2016). *Open Source Approach to Urban Growth
  Simulation*.
  Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci., XLI-B7,
  953-959. DOI: [10.5194/isprsarchives-XLI-B7-953-2016](https://doi.org/10.5194/isprsarchives-XLI-B7-953-2016)
- Sanchez, G.M., A. Petrasova, A., M.M. Skrip, E.L. Collins,
  M.A. Lawrimore, J.B. Vogler, A. Terando, J. Vukomanovic,
  H. Mitasova, and R.K. Meentemeyer. 2023.
  *Spatially interactive modeling of land change identifies location-specific
  adaptations most likely to lower future flood risk*.
   Sci Rep 13, 18869. DOI: [https://doi.org/10.1038/s41598-023-46195-9](https://doi.org/10.1038/s41598-023-46195-9)

## SEE ALSO

[FUTURES](r.futures.md),
[r.futures.simulation](r.futures.simulation.md),
[r.futures.parallelpga](r.futures.parallelpga.md),
[r.futures.devpressure](r.futures.devpressure.md),
[r.futures.potential](r.futures.potential.md),
[r.futures.potsurface](r.futures.potsurface.md),
[r.futures.demand](r.futures.demand.md),
[r.futures.calib](r.futures.calib.md),
[r.futures.gridvalidation](r.futures.gridvalidation.md)

For alternative validation metrics see
[r.confusionmatrix](r.confusionmatrix.md),
[r.kappa](r.kappa.md)

## AUTHORS

*Corresponding author:*
Anna Petrasova, akratoc ncsu edu,
[Center for Geospatial Analytics, NCSU](https://geospatial.ncsu.edu/)

*Original standalone version:*
Ross K. Meentemeyer,
Wenwu Tang,
Monica A. Dorning,
John B. Vogler,
Nik J. Cunniffe,
Douglas A. Shoemaker
(Department of Geography and Earth Sciences, UNC Charlotte)
Jennifer A. Koch
([Center for Geospatial Analytics, NCSU](https://geospatial.ncsu.edu/))

*Port to GRASS and GRASS-specific additions:*
Vaclav Petras,
[NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)

*Development pressure, demand, calibration, validation,
preprocessing tools and maintenance:*
Anna Petrasova,
[NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)

*Climate forcing submodel:*
Anna Petrasova,
[NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)  
Georgina Sanchez,
[Center for Geospatial Analytics, NCSU](https://geospatial.ncsu.edu/)

*Zoning:*
Margaret Lawrimore,
[Center for Geospatial Analytics, NCSU](https://geospatial.ncsu.edu/)  
Anna Petrasova,
[NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)
