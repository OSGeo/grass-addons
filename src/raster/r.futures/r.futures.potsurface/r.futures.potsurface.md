## DESCRIPTION

Module *r.futures.potsurface* is a support tool for computing
development probability surface based on maps and coefficients selected
by *[r.futures.potential](r.futures.potential.md)*. It computes the
initial probability surface used in the patch growing algorithm in
*[r.futures.pga](r.futures.pga.md)*. It is not necessary to use this
module, however it is useful to inspect the potential surface to better
understand the input data and how the predictors influence the
probability. The values range from 0 (unlikely to be developed) to 1
(high probability of development).

The inputs are the output file from
*[r.futures.potential](r.futures.potential.md)* and the name of the
**subregions** raster map.

## EXAMPLES

```sh
r.futures.potsurface input=potential.csv subregions=counties output=pot_surface
```

![image-alt](r_futures_potsurface.png)

Figure: We can visualize the potential surface in 3D and drape raster
representing developed (red) and undeveloped (green) cells over it.

## SEE ALSO

[FUTURES](r.futures.md), *[r.futures.pga](r.futures.pga.md)*,
*[r.futures.potential](r.futures.potential.md)*,
*[r.futures.devpressure](r.futures.devpressure.md)*,
*[r.futures.demand](r.futures.demand.md)*,
*[r.futures.calib](r.futures.calib.md)*,
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
