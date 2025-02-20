## DESCRIPTION

*r.sim.terrain* is a short-term landscape evolution model that simulates
topographic change for both steady state and dynamic flow regimes across
a range of spatial scales. It uses empirical models (RUSLE3D & USPED)
for soil erosion at watershed to regional scales and a physics-based
model (SIMWE) for shallow overland water flow and soil erosion at
subwatershed scales to compute short-term topographic change. This
either steady state or dynamic model simulates how overland sediment
mass flows reshape topography for a range of hydrologic soil erosion
regimes based on topographic, land cover, soil, and rainfall parameters.

## EXAMPLES

### Basic instructions

A basic example for the [North Carolina sample
dataset](https://grass.osgeo.org/download/data/). Install the add-on
module *r.sim.terrain*. Copy the raster elevation map *elev\_lid792\_1m*
from the PERMANENT mapset to the current mapset. Set the region to this
elevation map at 1 meter resolution. Run *r.sim.terrain* with the RUSLE
model for a 120 min event with a rainfall intensity of 50 mm/hr at a 3
minute interval. Set the empirical coefficients m and n to 0.4 and 1.3
respectively. Use the \`-f\` flag to fill depressions in order to reduce
the effect of positive feedback loops.

```sh
g.extension  extension=r.sim.terrain
g.copy raster=elev_lid792_1m@PERMANENT,elevation
g.region raster=elev_lid792_1m res=1
r.sim.terrain -f elevation=elevation runs=event mode=rusle_mode rain_intensity=50.0 rain_duration=120 rain_interval=3 m=0.4 n=1.3
```

![Net difference (m) for a dynamic RUSLE simulation](r_sim_terrain_rusle.png)  
*Figure: Net difference (m) for a dynamic RUSLE simulation of a 120 min
event with a rainfall intensity of 50 mm/hr with a 3 minute interval.*

### Spatially variable soil and landcover

Clone or download the [landscape evolution sample
dataset](https://github.com/baharmon/landscape_evolution_dataset) with a
time series of lidar-based digital elevation models and orthoimagery for
a highly eroded subwatershed of Patterson Branch Creek, Fort Bragg, NC,
USA.

Run *r.sim.terrain* with the simwe model for a 120 min event with a
rainfall intensity of 50 mm/hr. Use a transport value lower than the
detachment value to trigger a transport limited erosion regime. Use the
-f flag to fill depressions in order to reduce the effect of positive
feedback loops.

```sh
g.mapset -c mapset=transport location=nc_spm_evolution
g.region region=region res=1
r.mask vector=watershed
g.copy raster=elevation_2016@PERMANENT,elevation_2016
r.sim.terrain -f elevation=elevation_2016 runs=event mode=simwe_mode \
rain_intensity=50.0 rain_interval=120 rain_duration=10 walkers=1000000 \
detachment_value=0.01 transport_value=0.0001 manning=mannings runoff=runoff
```

![Net difference (m) for a steady state, transport limited SIMWE
simulation](r_sim_terrain.png)  
*Figure: Net difference (m) for a steady state, transport limited SIMWE
simulation of a 120 min event with a rainfall intensity of 50 mm/hr.*

For more detailed instructions and examples see this in-depth
[tutorial](https://github.com/baharmon/landscape_evolution/blob/master/tutorial.md).

## ERROR MESSAGES

If the module fails with

```sh
ERROR: Unable to insert dataset of type raster in the temporal database. The mapset of the dataset does not match the current mapset.
```

check that the input **elevation** map is in the current mapset. The
input **elevation** map must be in the current mapset so that it can be
registered in the temporal database.

## REFERENCES

  - Harmon, B. A., Mitasova, H., Petrasova, A., and Petras, V.:
    r.sim.terrain 1.0: a landscape evolution model with dynamic
    hydrology, Geosci. Model Dev., 12, 2837–2854,
    <https://doi.org/10.5194/gmd-12-2837-2019>, 2019.
  - Mitasova H., Barton M., Ullah I., Hofierka J., Harmon R.S., 2013.
    [3.9 GIS-Based Soil Erosion
    Modeling](https://www.sciencedirect.com/science/article/abs/pii/B978012374739600052X).
    In J. F. Shroder, ed. Treatise on Geomorphology. San Diego: Academic
    Press, pp. 228-258. DOI:
    <https://doi.org/10.1016/B978-0-12-374739-6.00052-X>.

## SEE ALSO

*[r.sim.water](https://grass.osgeo.org/grass-stable/manuals/r.sim.water.html),
[r.sim.sediment](https://grass.osgeo.org/grass-stable/manuals/r.sim.sediment.html)*

## AUTHOR

Brendan A. Harmon  
Louisiana State University  
*<brendan.harmon@gmail.com>*
