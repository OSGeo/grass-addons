## DESCRIPTION

*d.region.grid* plots a grid defined by the computational region or by a
raster map. The computational region can be the current computational
region or a saved computational region.

## EXAMPLES

### Comparing grids of two rasters

To compare how grids (resolutions) of two rasters align, here a digital
elevation model and a Landsat image, you can zoom to an area of interest
and show grids of both rasters. First, zoom close enough that the raster
cells become visible. Here a small saved region is used and a negative
value for *grow* causes *g.region* to zoom-in even more:

```sh
g.region region=rural_1m grow=-250 -p
```

Start a monitor (skip this in the GUI):

```sh
d.mon start=cairo width=600 height=400 output=two_rasters.png
```

Optionally, show the digital elevation model and its shaded relief
raster:

```sh
d.shade shade=elevation_shade color=elevation
```

Add grid for the elevation raster using a subtle color:

```sh
d.region.grid raster=elevation color="#9B520D"
```

Add grid for the Landsat raster using a high-contrast color:

```sh
d.region.grid raster=lsat7_2002_10 color=black
```

![Grids of two rasters which are not aligned](d_region_grid_two_rasters.png)  
*Figure: Grids of two rasters which are not aligned*

If you are using *d.mon*, you can stop the monitor using:

```sh
d.mon stop=cairo
```

### Showing the current computational region grid

Let's say you want to render grid cells of a computational region you
plan to resample a raster map into. First, set the computational region
to the raster map, then start the monitor (here we use file-based
rendering in the command line with the cairo driver), and finally,
render the raster map:

```sh
g.region raster=elevation
d.mon start=cairo width=600 height=400 output=new_region_grid.png
d.rast map=elevation
```

Then change to the desired computational region, here the new region
resolution is set to 1000 meters (map units) and fitted into the current
region extent without modifying the 1000 meters value.

```sh
g.region res=1000 -a
```

Now, you are ready to plot the grid of the current computational region:

```sh
d.region.grid -r
```

![image-alt](d_region_grid_new_region_grid.png)

*Figure: Raster with resolution 10 meters and grid of a computational
region with resolution 1000 meters*

Assuming you used *d.mon* to start rendering as in the code above, you
can stop it using:

```sh
d.mon stop=cairo
```

### Using an existing saved region

Displaying a saved computational region is extremely helpful in GUI,
were you save the current region first:

```sh
g.region save=study_area
```

Then, you use *Add command layer* to add the following command:

```sh
d.region.grid region=study_area
```

## NOTES

  - Use through the *Add command layer* option in the GUI.
  - In the GUI, it is currently not possible to directly draw the
    current region.
  - Generally, only the grid resolution is based on the selected region
    or raster, with extent of the grid being limited only by what is
    being displayed (this happens to be the current computational region
    when rendering directly to files in command line).

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[d.grid](https://grass.osgeo.org/grass-stable/manuals/d.frame.html),
[d.rast.num](https://grass.osgeo.org/grass-stable/manuals/d.rast.num.html),
[d.mon](https://grass.osgeo.org/grass-stable/manuals/d.mon.html),
[v.mkgrid](https://grass.osgeo.org/grass-stable/manuals/v.mkgrid.html)*

## AUTHOR

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
