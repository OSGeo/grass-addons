## DESCRIPTION

*r.sun.daily* is a convenient script for running r.sun for multiple days
in a loop. It corresponds to mode 2 (aggregation mode, see r.sun [manual
page](https://grass.osgeo.org/grass-stable/manuals/r.sun.html)).

### Output parameters explanation

There are two basic options:

- output series of maps (one for each day): options containing
    basename in their name
- output one map which is an aggregation of the intermediate maps

You can choose any combination of parameters: e.g. total map of diffuse
radiance and series of beam radiance maps. Series of maps are (if flag
*t* is checked) registered to space time raster dataset with relative
time and point time (not interval time). For GRASS 6, only timestamp is
assigned.

## EXAMPLE

```sh
g.region raster=elevation -p
r.sun.daily elevation=elevation start_day=30 end_day=40 \
            beam_rad_basename=beam beam_rad=beam_sum nprocs=4 -t
# show information about newly created space time dataset
t.info beam

# show information about newly created beam_sum raster map
r.info beam
```

## SEE ALSO

*[r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html)  
[r.sun.hourly](r.sun.hourly.md) in Addons*

## AUTHORS

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/),  
Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
