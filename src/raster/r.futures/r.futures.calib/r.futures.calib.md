## DESCRIPTION

Tool *r.futures.calibration* is part of [FUTURES](r.futures.md), land
change model. It is used for calibrating certain input variables for
patch growing algorithm *r.futures.simulation*, specifically patch size
and compactness parameters. The calibration process is conducted to
match observed urban growth patterns to those simulated by the model,
including the sizes and shapes of new development. The calibration is
achieved by varying the values of the patch parameters, comparing the
distribution of simulated patch sizes to those observed for the
reference period, and choosing the values that provide the closest
match. For the details about calibration see below.

### Patch size

As part of the calibration process, tool *r.futures.calibration*
produces patch size distribution file specified in **patch_sizes**
parameter, which contains sizes (in cells) of all new patches observed
in the reference period. The format of this file is one patch size per
line. If flag **-s** is used, patch sizes will be analyzed per each
subregion, and written as a CSV file with columns representing patch
library for each subregion and header containing the categories of
subregions. FUTURES uses this file to determine the size of the
simulated patches. Often the length of the reference time period does
not match the time period which we are trying to simulate. We use the
**discount factor** to alter the size of simulated patches so that after
the reference period they closely match the observed patterns. During
the simulation, this factor is multiplied by the patch sizes listed in
the patch size file. The values of **discount factor** can vary between
0 and 1, for example value 0.6 was used by Meentemeyer et al. 2013.

### Patch compactness

The shapes of patches simulated by FUTURES are governed by the patch
compactness parameter (Meentemeyer et al. 2013, Eq. 1). This variable
doesn't represent actual patch compactness, it is rather an adjustable
scaling factor that controls patch compactness through a distance decay
effect. By specifying the mean and range of this parameter in tool
*r.futures.simulation*, we allow for variation in patch shape. As the
value of the parameter increases, patches become more compact.
Calibration is achieved by varying the values specified in
**compactness_mean** and **compactness_range** and comparing the
distribution of the simulated patch compactness (computed as
`patch perimeter / (2 * sqrt(pi * area))`) to those observed for the
reference period. Meentemeyer et al. 2013 used mean 0.4 and range 0.08.

### Calibration input and output

Calibration requires the development binary raster in the beginning and
end of the reference period (**development_start** and
**development_end**) to derive the patch sizes and compactness. It is
possible to set the minimum number of cells of a patch in
**patch_threshold** to ignore too small patches. For each combination of
values provided in **compactness_mean**, **compactness_range** and
**discount_factor**, it runs tool *r.futures.simulation* which creates
new development pattern. From this new simulated development, patch
characteristics are derived and compared with the observed
characteristics by histogram comparison and an error (histogram
distance) is computed. Since *r.futures.simulation* is a stochastic
tool, multiple runs (specified in **repeat**) are recommended, the
error is then averaged. Calibration results are saved in a CSV file
specified in **calibration_results**:

```text
discount_factor,compactness_mean,compactness_range,area_error,compactness_error,combined_error
0.10,0.60,0.10,0.92,0.70,0.81
0.10,0.80,0.10,0.92,0.76,0.84
0.10,0.20,0.10,0.93,0.78,0.85
0.10,0.50,0.10,0.89,0.82,0.86
0.10,1.00,0.10,0.94,0.84,0.89
0.10,0.90,0.10,0.92,0.86,0.89
0.10,0.70,0.10,0.96,0.83,0.90
0.10,0.10,0.10,1.00,1.00,1.00
```

The first three columns represent the combination of calibrated
parameters. The last column is the average of the normalized area and
compactness errors for each combination. The first line shows the
combination with lowest error.

Providing too many values in **compactness_mean**, **compactness_range**
and **discount_factor** results in very long computation. Therefore it
is recommended to run *r.futures.calibration* on high-end computers,
with more processes running in parallel using **nprocs** parameter.
Also, it can be run on smaller regions, under the assumption that patch
sizes and shapes are close to being consistent across the entire study
area.

For all other parameters not mentioned above, please refer to
*r.futures.simulation* documentation.

## REFERENCES

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

[FUTURES overview](r.futures.md),
[r.futures.simulation](r.futures.simulation.md),
[r.futures.parallelpga](r.futures.parallelpga.md),
[r.futures.devpressure](r.futures.devpressure.md),
[r.futures.demand](r.futures.demand.md),
[r.futures.potential](r.futures.potential.md),
[r.futures.potsurface](r.futures.potsurface.md),
[r.futures.gridvalidation](r.futures.gridvalidation.md),
[r.futures.validation](r.futures.validation.md),
[r.sample.category](r.sample.category.md),
[r.object.geometry](r.object.geometry.md)

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
