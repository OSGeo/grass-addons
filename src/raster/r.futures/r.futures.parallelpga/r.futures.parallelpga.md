## DESCRIPTION

Since FUTURES model is stochastic, multiple runs are recommended. Module
*r.futures.parallelpga* is a script for running
[r.futures.pga](r.futures.pga.md) on multiple CPUs. All options of
[r.futures.pga](r.futures.pga.md) are available (except for random seed
options which are handled by *r.futures.parallelpga*).

Option **repeat** changes the number of times the simulation is repeated
with the same settings but different random seed. Option **nprocs** sets
the number of parallel processes to be used, which depends on number of
available CPUs. Flag **-d** switches on parallelization on subregion
level. Subregions are split and simulation runs on each subregion
individually. This approach is convenient if available memory is not
sufficient for the entire study area. However, as each subregion is
handled separately, development pressure on the edge of a subregion does
not influence its neighbors. This can influence the results in case of
significant development happening on the subregion boundary.

## EXAMPLES

## SEE ALSO

[FUTURES](r.futures.md), *[r.futures.pga](r.futures.pga.md)*,
*[r.futures.devpressure](r.futures.devpressure.md)*,
*[r.futures.potsurface](r.futures.potsurface.md)*,
*[r.futures.demand](r.futures.demand.md)*,
*[r.futures.calib](r.futures.calib.md)*,
*[r.futures.potential](r.futures.potential.md)*,
*[r.sample.category](r.sample.category.md)*

## REFERENCES

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

Anna Petrasova, [NCSU GeoForAll](https://geospatial.ncsu.edu/geoforall/)
