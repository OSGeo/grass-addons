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

```text
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

## SEE ALSO

For alternative validation metrics see
[r.confusionmatrix](r.confusionmatrix.html),
[r.kappa](r.kappa.html)

## REFERENCES

- Robert Gilmore Pontius Jr & Marco Millones (2011).
  [Death to Kappa: birth of quantity disagreement and allocation disagreement for accuracy
  assessment](https://doi.org/10.1080/01431161.2011.552923).
  International Journal of Remote Sensing, 32:15, 4407-4429
- Jasper van Vliet, Arnold K. Bregt, Alex Hagen-Zanker (2011)
  [Revisiting Kappa to account for change in the accuracy assessment of land-use change
  models](https://doi.org/10.1016/j.ecolmodel.2011.01.017).
  Ecological Modelling, Volume 222, Issue 8.
- Meentemeyer, R. K., Tang, W., Dorning, M. A., Vogler, J. B.,
  Cunniffe, N. J., & Shoemaker, D. A. (2013).
  [FUTURES: Multilevel Simulations of Emerging Urban-Rural Landscape Structure Using a Stochastic Patch-Growing
  Algorithm](https://doi.org/10.1080/00045608.2012.707591).
  Annals of the Association of American Geographers, 103(4), 785-807.
  DOI: 10.1080/00045608.2012.707591
- Dorning, M. A., Koch, J., Shoemaker, D. A., & Meentemeyer, R. K. (2015).
  [Simulating urbanization scenarios reveals tradeoffs between conservation planning
  strategies](https://doi.org/10.1016/j.landurbplan.2014.11.011).
  Landscape and Urban Planning, 136, 28-39.
  DOI: 10.1016/j.landurbplan.2014.11.011
- Petrasova, A., Petras, V., Van Berkel, D., Harmon, B. A.,
  Mitasova, H., & Meentemeyer, R. K. (2016).
  [Open Source Approach to Urban Growth
  Simulation](https://isprs-archives.copernicus.org/articles/XLI-B7/953/2016/isprs-archives-XLI-B7-953-2016.pdf).
  Int. Arch. Photogramm. Remote Sens. Spatial Inf. Sci., XLI-B7, 953-959.
  DOI: 10.5194/isprsarchives-XLI-B7-953-2016

## AUTHOR

Anna Petrasova, [NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)
