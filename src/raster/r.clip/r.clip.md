## DESCRIPTION

The module extracts portion of the **input** raster map according to the
current computational region. The areas outside of the computational
region are clipped and only the inner part is kept. The **input** raster
map is left intact and a new (clipped) **output** raster map is created
in the process.

By default the cell size and the cell alignment of the original raster
are preserved. In other words, the output map inherits its resolution
and cell positions (grid) from the input raster rather than the
computational region.

If resampling into the cells size and cell alignment of the current
computational is desired, the module can perform a nearest neighbor
resampling when the **-r** flag is used. If a more advanced resampling
is required, the user is advised to use one of the dedicated resampling
modules.

If mask
(*[r.mask](https://grass.osgeo.org/grass-stable/manuals/r.mask.html)*)
is active, it is respected and the output raster map will contain NULL
(no data) values according to the mask. Otherwise, values in the
**input** raster map are simply transferred to the **output** raster
map.

The color table of the output raster map is set according to the input
raster map, so that the colors in both raster maps will match.

## NOTES

- In GRASS GIS, clipping of rasters is usually not needed because
    modules respect the current computational region and clipping (with
    possible resampling) is done automatically.
- If the user needs to clip raster map according to another raster map
    or according to a vector map, the
    *[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*
    should be used first before running the *r.clip* module.
- The extent of the resulting map might be slightly different based on
    how the cells of the input raster align with the cells of the
    computational region. The mechanism for aligning in the background
    is the one used in
    *[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*.
    If an exact match is desired, the user is advised to resolve the
    cell alignment ahead using
    *[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html)*
    and then use *r.clip* with the **-r** flag.

## EXAMPLES

The following examples are using the full North Carolina sample
location.

### Clip according to a raster map

First we set the computational region to match the raster map called
*elev\_lid792\_1m* which we want to use for clipping:

```sh
g.region raster=elev_lid792_1m
```

Now, the following will clip raster map called *elevation* according to
the extent of *elev\_lid792\_1m* raster map creating a new raster map
called *elevation\_clipped*:

```sh
r.clip input=elevation output=elevation_clipped
```

### Clip and then compare the resolutions

The following example clips (crops) raster map called *elevation*
according to the current region resulting in a new raster map called
*clipped\_elevation*. The computational region will be set match raster
map called *elev\_lid792\_1m* since this the extent we want to work with
in this example.

First we set the computational region to match a raster map called
*elev\_lid792\_1m*:

```sh
g.region raster=elev_lid792_1m
```

This is the computational region we want to have. Now we check the new
region using:

```sh
g.region -g
```

In the output, we can see extent, resolution in both directions, and
number of rows and columns:

```text
...
n=220750
s=220000
w=638300
e=639000
nsres=1
ewres=1
rows=750
cols=700
cells=525000
...
```

Now we perform the clipping:

```sh
r.clip input=elevation output=clipped_elevation
```

Finally, we check the size of the new raster map using:

```sh
r.info map=clipped_elevation -g
```

In the output, we can see that the extent is the same (exactly the same
in this case) as the computational region while the resolution and
number of cells are different:

```text
...
north=220750
south=220000
east=639000
west=638300
nsres=10
ewres=10
rows=75
cols=70
cells=5250
...
```

The reason for this is that the *elevation* map was not resampled,
instead the cell values and positions were preserved. The number of
cells depends on the resolution which was derived from the original
*elevation* map. To see it, we can use the following:

```sh
r.info map=elevation -g
```

The output shows the resolution used for the new *clipped\_elevation* as
well as much higher number of cells and larger extent of the original
map:

```text
...
north=228500
south=215000
east=645000
west=630000
nsres=10
ewres=10
rows=1350
cols=1500
cells=2025000
...
```

## SEE ALSO

*[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[g.copy](https://grass.osgeo.org/grass-stable/manuals/g.copy.html),
[r.mask](https://grass.osgeo.org/grass-stable/manuals/r.mask.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[r.proj](https://grass.osgeo.org/grass-stable/manuals/r.proj.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.resample](https://grass.osgeo.org/grass-stable/manuals/r.resample.html),
[r.resamp.rst](https://grass.osgeo.org/grass-stable/manuals/r.resamp.rst.html),
[v.clip](https://grass.osgeo.org/grass-stable/manuals/v.clip.html)*

## AUTHOR

Vaclav Petras, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/)
