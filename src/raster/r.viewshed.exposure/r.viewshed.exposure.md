## DESCRIPTION

*r.viewshed.exposure* computes visual exposure to given exposure
source(s) using weighted (optional) parametrised (optional) cumulative
viewshed.

### The algorithm

The processing workflow of the module consists of five steps:

1. Random sampling of exposure source raster map with vector points,
2. Calculating binary viewshed for each exposure source point,
3. Optional parametrisation of the binary viewshed,
4. Optional weighting of the (parametrised) viewshed,
5. Cumulating the (weighted) (parametrised) viewsheds.

[![image-alt](r_viewshed_exposure_workflow.png)](r_viewshed_exposure_workflow.png)  
*Processing workflow*

#### 1\. Random sampling of exposure source raster map with vector points

To improve computational efficiency, the exposure source raster map is
randomly sampled with defined density (0-100%; option
**sample\_density**). In general, lower sampling densities lead to lower
accuracy, higher uncertainty of the result and lower processing time,
while higher sampling densities lead to higher accuracy, lower
uncertainty of the result and longer processing time. Alternatively, it
is possible to replace the exposure source raster map with own vector
map of exposure source points (option **sampling\_points**).

#### 2\. Binary viewshed for each exposure source point

A binary viewshed for each exposure source point is calculated using
[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html)
module. The height of exposure source point above the surface is 0m. The
height of observer point (exposure receiver) above the surface is
specified by option **observer\_elevation**. Viewshed radius (range of
visual exposure) is specified by option **max\_distance**.

#### 3\. (optional) Parametrisation of the binary viewshed

The module supports different parametrization functions to better
reflect human visual perspective by accounting for the variable
contribution of the exposure source pixels to visual exposure depending
on their distance, slope and aspect relative to the observer (option
**function**). Four parametrisation functions are implemented: *distance
decay function*, *fuzzy viewshed function*, *visual magnitude function*
and *solid angle function*.

In *distance decay function*, the contribution of an exposure source
pixel *xi* to visual exposure at the observer pixel decreases in
proportion to the square of distance between the exposure source pixel
and the observer: *D(xi) = A/v<sup>2</sup>*; *A* is the area of the
exposure source pixel, *v* is the distance between the exposure source
pixel and the observer. See Grêt-Regamey et al. (2007) and Chamberlain
and Meitner (2013) for more details.

In *fuzzy viewshed function*, the contribution of an exposure source
pixel *xi* to visual exposure at the observer pixel depends on the
distance between the exposure source pixel and the observer and the
radius of perfect clarity. See Fisher (1994) and Ogburn (2006) for more
details.

In *visual magnitude function*, the contribution of an exposure source
pixel *xi* to visual exposure at the observer pixel depends on the
pixel's slope, aspect and distance relative to the observer. See
Chamberlain and Meitner (2013) for more details.

In *solid angle function*, the contribution of an exposure source pixel
*xi* to visual exposure at the observer pixel is calculated as a solid
angle, i.e. the area (in sterradians) of the observer's eye retina
covered by the exposure source pixel. See Domingo-Santos et al. (2011)
for more details.

#### 4\. (optional) Weighting of the (parametrised) viewshed

Weighting of the individual (parametrised) viewsheds enables modelling
variable intensities of the exposure sources. The individual viewsheds
are multiplied by values extracted from the weights raster map (option
**weights**) at the exposure source points.

#### 5\. Cumulating the (weighted) (parametrised) viewsheds

After each iteration, the partial viewsheds are cumulated (added),
resulting in a raster of (weighted) (parametrised) cumulative viewshed.
This raster represents visual exposure to the exposure source.

### Memory and parallel processing

Options **memory** specifies the amount of memory allocated for viewshed
computation. Option **nprocs** specifies the number of cores used in
parallel processing. In parallel processing, the computation of
individual viewsheds is randomly distributed across the specified cores.

## EXAMPLES

Computation of visual exposure to major roads in South-West Wake county,
North Carolina. Input data are a terrain model and a raster map of major
roads from NC dataset. Viewshed parametrisation function is set to none
(example 1) and solid angle (example 2). Sampling density is set to 50%,
exposure range to 2km.

```sh
# set computation region to terrain model
g.region raster=elevation@PERMANENT

# calculate visual exposure
# no viewshed parametrisation function (binary viewshed)
r.viewshed.exposure input=elevation@PERMANENT
  output=exposure_roadsmajor_b
  source=roadsmajor@PERMANENT
  observer_elevation=1.50
  max_distance=2000
  sample_density=50 memory=5000 nprocs=25

# calculate visual exposure
# solid anfle viewshed parametrisation function
r.viewshed.exposure input=elevation@PERMANENT
  output=exposure_roadsmajor_s
  source=roadsmajor@PERMANENT
  observer_elevation=1.50
  max_distance=2000
  function=solid_angle
  sample_density=50 memory=5000 nprocs=25

# scale solid angle values for visualisation purposes
# (see Domingo-Santos et al., 2011)
r.mapcalc expression=exposure_roadsmajor_s_rescaled =
  if(exposure_roadsmajor_s@user1>=0.2*3.1416,1,1/
  (-1* log(exposure_roadsmajor_s@user1 /(2*3.1416))))
```

[![image-alt](r_viewshed_exposure_example_binary.png)](r_viewshed_exposure_example_binary.png)  
*Example of r.viewshed.exposure (1)*

[![image-alt](r_viewshed_exposure_example_solid_angle.png)](r_viewshed_exposure_example_solid_angle.png)  
*Example of r.viewshed.exposure (2)*

## TODO

- Implement variable exposure source height.
- Implement possibility to switch between absolute and relative values
    of visual exposure (now absolute).

## REFERENCES

- Cimburova, Z., Blumentrath, S., 2022. Viewshed-based modelling of
    visual exposure to urban greenery - an efficient GIS tool for
    practical applications. *Landscape and Urban Planning* 222, 104395.
    <https://doi.org/10.1016/j.landurbplan.2022.104395>
- Chamberlain, B.C., Meitner, M.J., 2013. A route-based visibility
    analysis for landscape management. *Landscape and Urban Planning*
    111, 13-24. <https://doi.org/10.1016/j.landurbplan.2012.12.004>
- Domingo-Santos, J.M., de Villarán, R.F., Rapp-Arrarás, Í., de
    Provens, E.C.-P., 2011. The visual exposure in forest and rural
    landscapes: An algorithm and a GIS tool. *Landscape and Urban
    Planning* 101, 52-58.
    <https://doi.org/10.1016/j.landurbplan.2010.11.018>
- Fisher, P., 1994. Probable and fuzzy models of the viewshed
    operation, in: Worboys, M.F. (Ed.), *Innovations in GIS*. Taylor &
    Francis, London, pp. 161-176.
- Grêt-Regamey, A., Bishop, I.D., Bebi, P., 2007. Predicting the
    scenic beauty value of mapped landscape changes in a mountainous
    region through the use of GIS. *Environment and Planning B: Planning
    and Design* 34, 50-67. <https://doi.org/10.1068/b32051>
- Ogburn, D.E., 2006. Assessing the level of visibility of cultural
    objects in past landscapes. *Journal of Archaeological Science* 33,
    405-413. <https://doi.org/10.1016/j.jas.2005.08.005>

## SEE ALSO

*[r.viewshed](https://grass.osgeo.org/grass-stable/manuals/r.viewshed.html),
[r.viewshed.cva](r.viewshed.cva.md), [r.survey](r.survey.md)*

## AUTHORS

Zofie Cimburova, [NINA](https://www.nina.no)  
Stefan Blumentrath, [NINA](https://www.nina.no)
