## DESCRIPTION

*r.sun.hourly* is a convenient script for running r.sun for multiple
times in a loop. It allows to run r.sun in mode 1 to create maps of
instantaneous solar irradiance. Alternatively, it allows to integrate
solar irradiance maps over specified time period to compute solar
irradiation (mode 2). See r.sun [manual
page](https://grass.osgeo.org/grass-stable/manuals/r.sun.html) for more
information.

### Output parameters explanation

There are three basic types of output:

In mode 1, if one of options **beam\_rad\_basename**,
**diff\_rad\_basename** **refl\_rad\_basename**,
**glob\_rad\_basename**, and **incidout\_basename** is selected, it will
compute a time series of irradiance maps. Optionally, **b** flag will
convert them to binary rasters representing shaded areas. Using this
flag in combination with **beam\_rad\_basename** is a convenient way to
determine if there is direct sunlight or not at a certain place and
time. Series of maps are (if flag **t** is checked) registered to space
time raster dataset with absolute time and point time (not interval
time). Option **year** has to be specified so that the raster maps can
be registered to space time dataset or assigned a timestamp. The reason
is that it is not possible to assign time without date.

In mode 2, a series of solar irradiation maps will be computed with
units Wh/m2. This is done by multiplying an instantaneous irradiance
raster computed in the middle of the specified intervals by time step.
For example, if **start\_time** is 8, **end\_time** is 10 and
**time\_step** is 0.5, the irradiation rasters will be computed for
times 8:15, 8:45, 9:15 and 9:45.

If flag **c** is selected it will accumulate the irradiation values,
meaning the last raster represents all solar irradiation during the
period.

When any of output options **beam\_rad**, **diff\_rad** **refl\_rad**
and **glob\_rad** are specified, irradiation rasters are summed over the
specified period (mode 2 only).

### Real-sky radiation parameters

Real-sky radiation parameters (see
[r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html)) can be
input as raster map (**coeff\_bh** and **coeff\_dh**), or space-time
raster dataset (**coeff\_bh\_strds** and **coeff\_dh\_strds**) to
account for time-varying conditions. The space-time raster dataset
(strds) needs to be interval-based (i.e. have start and end time, see
[t.register](https://grass.osgeo.org/grass-stable/manuals/t.register.html),
for more details).

## EXAMPLES

Calculate for current region the beam irradiance (direct radiation) for
DOY 355 in 2014 from 8am to 3pm:

```sh
g.region -p
r.sun.hourly elevation=elevation start_time=8 end_time=15 \
              day=355 year=2014 beam_rad_basename=beam nprocs=4 -t
# show information about newly created space time dataset
t.info beam

# show raster maps registered in beam temporal dataset
t.rast.list beam
```

Calculate beam irradiation during day and also cumulative irradiation,
use different steps:

```sh
g.region raster=elevation res=100 -pa
r.sun.hourly elevation=elevation year=2019 day=100  start=8 end=16 time_step=0.333 beam_rad_basename=beam_m2_step_short mode=mode2 nprocs=4 -t
r.sun.hourly elevation=elevation year=2019 day=100  start=8 end=16 time_step=0.333 beam_rad_basename=beam_m2_step_short_cum mode=mode2 nprocs=4 -tc
r.sun.hourly elevation=elevation year=2019 day=100  start=8 end=16 time_step=1 beam_rad_basename=beam_m2_step_long mode=mode2 nprocs=4 -t
r.sun.hourly elevation=elevation year=2019 day=100  start=8 end=16 time_step=1 beam_rad_basename=beam_m2_step_long_cum mode=mode2 nprocs=4 -tc
g.gui.tplot strds=beam_m2_step_short,beam_m2_step_long,beam_m2_step_short_cum,beam_m2_step_long_cum coordinates=636919,220431
```

[![image-alt](r_sun_hourly.png)](r_sun_hourly.png)

## NOTE

Beam irradiance binary raster maps can be displayed as semitransparent
over other map layers or module
[*r.null*](https://grass.osgeo.org/grass-stable/manuals/r.null.html) can
be used to set one of the values (either shade or sunlight) as NULL.

## SEE ALSO

*[r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html),
[r.sun.daily](r.sun.daily.md) in Addons*

## AUTHORS

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/),  
Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
