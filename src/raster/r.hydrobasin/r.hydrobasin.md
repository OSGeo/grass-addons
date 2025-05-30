## DESCRIPTION

*r.hydrobasin* delineates a large number of watersheds from a flow
direction raster map and an outlets vector map using the
Memory-Efficient Watershed Delineation (MESHED) OpenMP parallel
algorithm by Cho (2025).

## NOTES

*r.hydrobasin* uses a flow direction raster map and an outlets vector
map to delineate a large number of watersheds in parallel using OpenMP.

The module recognizes three different formats of flow directions:

![image-alt](r_hydrobasin_formats.png)

*r.watershed* can be used to create an input flow direction raster map.
It can also create watersheds, but it uses an elevation map instead of a
flow direction map, which is actually one of its outputs, and does not
take outlets as input. *r.hydrobasin* is more similar to
*r.water.outlet* and *r.stream.basins*. Both modules take an input flow
direction map from *r.watershed*, but *r.water.outlet* can delineate a
watershed for one outlet point at a time and *r.stream.basins* is a
sequential module for multiple watersheds. Unlike *r.stream.basins*,
*r.hydrobasin* can use a column for watershed IDs, but using a
non-default column is slower than using the default category (cat)
column because of database queries.

For comparisons, using an i7-1370P CPU with 64GB memory and a 30-meter
flow direction map for the entire Texas (1.8 billion cells),
*r.hydrobasin* took 1 minute 27 seconds to delineate the entire state
using 60,993 outlet cells draining away (see below how to extract
draining cells) while *r.stream.basins* 5 minutes 28 seconds, both using
the category column. However, *r.hydrobasin* with a non-category column
took 6 minutes 21 seconds because of heavy database queries.

## EXAMPLES

These examples use the North Carolina sample dataset.

Calculate flow accumulation using *r.watershed* and delineate all
watersheds from draining cells using *r.hydrobasin*:

```sh
# set computational region
g.region -ap raster=elevation

# calculate drainage directions using r.watershed
r.watershed -s elevation=elevation drainage=drain

# extract draining cells
r.mapcalc ex="dcells=if(\
        (isnull(drain[-1,-1])&&abs(drain)==3)||\
        (isnull(drain[-1,0])&&abs(drain)==2)||\
        (isnull(drain[-1,1])&&abs(drain)==1)||\
        (isnull(drain[0,-1])&&abs(drain)==4)||\
        (isnull(drain[0,1])&&abs(drain)==8)||\
        (isnull(drain[1,-1])&&abs(drain)==5)||\
        (isnull(drain[1,0])&&abs(drain)==6)||\
        (isnull(drain[1,1])&&abs(drain)==7),1,null())"
r.to.vect input=dcells type=point output=dcells

# delineate all watersheds using r.hydrobasin
r.hydrobasin dir=drain outlets=dcells output=wsheds nprocs=$(nproc)
```

![image-alt](r_hydrobasin_wsheds.png)

Perform the same analysis for 10,938 bridges in North Carolina:

```sh
# set computational region
g.region -ap raster=elev_state_500m

# calculate drainage directions using r.watershed
r.watershed -s elevation=elev_state_500m drainage=drain_state

# delineate all watersheds using r.hydrobasin
r.hydrobasin dir=drain_state outlets=bridges output=bridge_wsheds nproc=$(nproc)
```

![image-alt](r_hydrobasin_bridge_wsheds.png)

## SEE ALSO

*[r.flowaccumulation](r.flowaccumulation.md),
[r.accumulate](r.accumulate.md),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[r.stream.extract](https://grass.osgeo.org/grass-stable/manuals/r.stream.extract.html),
[r.stream.distance](r.stream.distance.md)*

## REFERENCES

Huidae Cho, January 2025. *Avoid Backtracking and Burn Your Inputs:
CONUS-Scale Watershed Delineation Using OpenMP.* Environmental Modelling
& Software 183, 106244.
[doi:10.1016/j.envsoft.2024.106244](https://doi.org/10.1016/j.envsoft.2024.106244).

## AUTHOR

[Huidae Cho](mailto:grass4u@gmail-com), New Mexico State University
