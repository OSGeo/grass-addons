## DESCRIPTION

The *r.random.walk* module generates a 2D random walk across the current
computational region. The module provides control of the number of steps
and directions (4 or 8) a walker can take and allows the walker's
behavior to be set to be self-avoiding (Madras et al., 1996) or allow
revisits. The output displays the frequency the walker visited each cell
or the average frequency. The module can run multiple walks in parallel.
It either samples the same starting location for each walk or generates
a unique starting position for each walker.

## EXAMPLE

Using the North Carolina full sample dataset:

```sh
# set computational region
g.region raster=elevation -p

# calculate smoothed random walk from a single starting locations.
r.random.walk -at output=random_walk_smooth_paths directions=8 steps=100000 memory=1800 seed=1 nprocs=6 nwalkers=100
```

![image-alt](r_random_walk_example.png)  
Smoothed random walk (Single Starting Location)

```sh
# calculate smoothed random walk from a multiple starting locations.
r.random.walk -as output=random_walk_smooth directions=8 steps=100000 memory=1800 nprocs=6 nwalkers=100
```

![image-alt](r_random_walk_example_2.png)  
Smoothed random walk (Multiple Starting Locations)

## SEE ALSO

[r.surf.fractal](https://grass.osgeo.org/grass-stable/manuals/r.surf.fractal.html),
[r.surf.random](https://grass.osgeo.org/grass-stable/manuals/r.surf.random.html)

## AUTHOR

Corey T. White, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
