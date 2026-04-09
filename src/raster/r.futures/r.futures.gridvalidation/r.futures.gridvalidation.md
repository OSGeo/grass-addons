## DESCRIPTION

Tool *r.futures.gridvalidation* allows to
validate land change simulation results spatially.
It is a wrapper around
[r.futures.validation](r.futures.validation.html)
that computes validation metrics for each cell of a grid
or for each polygon of a vector layer.
It computes:

- Allocation disagreement (total and per class),
  see Pontius et al, 2011
- Quantity disagreement (total and per class),
  see Pontius et al, 2011
- Cohen's Kappa
- Kappa simulation, see van Vliet et al, 2011

When **original** is provided and the input rasters contain
only binary categories (0 for undeveloped and 1 for developed),
the tool additionally computes change detection metrics
(see [r.futures.validation](r.futures.validation.html)
for details).
When more than two categories are present,
these metrics are skipped.

The tool operates in two modes:

- **Grid mode** (**region**):
  A saved region is divided into grid cells and metrics
  are computed for each cell. Cell size of the region
  should be larger than the cell size of the current
  computational region. The output is a point vector
  layer with each point at the center of a grid cell.
- **Subregion mode** (**subregions**):
  Metrics are computed for each polygon of the input
  vector layer. The output is a copy of the input vector
  with metrics added as attribute columns.

This tool can be used for any number of classes.
Input raster **original** represents the initial conditions
and is needed for Kappa simulation and for change
detection metrics.

## EXAMPLES

Validate FUTURES output by computing validation metrics
on a 5km grid.
First, reclassify FUTURES output
(where -1 is undeveloped, 0 is initially developed,
and 1 to N is the step when a cell became developed)
to binary (0 = undeveloped, 1 = developed).
Create a file `reclass_rules.txt` with the following
content:

```text
-1 = 0 undeveloped
0 thru 1000 = 1 developed
```

Then save a region used as a grid and reclassify:

```text
g.region res=5000 -a save=grid
r.reclass input=simulated_2016 output=simulated_2016_reclass rules=reclass_rules.txt
```

Run the grid validation:

```text
r.futures.gridvalidation simulated=simulated_2016_reclass reference=reference_2016 \
    original=orig_2001 output=validation_grid region=grid nprocs=4
```

## SEE ALSO

[r.futures.validation](r.futures.validation.html),
[FUTURES](r.futures.html),
[r.futures.simulation](r.futures.simulation.html),
[r.futures.potential](r.futures.potential.html),
[r.futures.devpressure](r.futures.devpressure.html),
[r.futures.demand](r.futures.demand.html),
[r.futures.calib](r.futures.calib.html),
[r.sample.category](r.sample.category.html)

## REFERENCES

- Robert Gilmore Pontius Jr & Marco Millones (2011).
  [Death to Kappa: birth of quantity disagreement
  and allocation disagreement for accuracy
  assessment](https://doi.org/10.1080/01431161.2011.552923).
  International Journal of Remote Sensing,
  32:15, 4407-4429
- Jasper van Vliet, Arnold K. Bregt,
  Alex Hagen-Zanker (2011)
  [Revisiting Kappa to account for change in the
  accuracy assessment of land-use change
  models](https://doi.org/10.1016/j.ecolmodel.2011.01.017).
  Ecological Modelling, Volume 222, Issue 8.
- Meentemeyer, R. K., Tang, W., Dorning, M. A.,
  Vogler, J. B., Cunniffe, N. J.,
  & Shoemaker, D. A. (2013).
  [FUTURES: Multilevel Simulations of Emerging
  Urban-Rural Landscape Structure Using a Stochastic
  Patch-Growing
  Algorithm](https://doi.org/10.1080/00045608.2012.707591).
  Annals of the Association of American Geographers,
  103(4), 785-807.
  DOI: 10.1080/00045608.2012.707591
- Dorning, M. A., Koch, J., Shoemaker, D. A.,
  & Meentemeyer, R. K. (2015).
  [Simulating urbanization scenarios reveals
  tradeoffs between conservation planning
  strategies](https://doi.org/10.1016/j.landurbplan.2014.11.011).
  Landscape and Urban Planning, 136, 28-39.
  DOI: 10.1016/j.landurbplan.2014.11.011
- Petrasova, A., Petras, V., Van Berkel, D.,
  Harmon, B. A., Mitasova, H.,
  & Meentemeyer, R. K. (2016).
  [Open Source Approach to Urban Growth
  Simulation](https://isprs-archives.copernicus.org/articles/XLI-B7/953/2016/isprs-archives-XLI-B7-953-2016.pdf).
  Int. Arch. Photogramm. Remote Sens. Spatial
  Inf. Sci., XLI-B7, 953-959.
  DOI: 10.5194/isprsarchives-XLI-B7-953-2016

## AUTHOR

Anna Petrasova,
[NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)
