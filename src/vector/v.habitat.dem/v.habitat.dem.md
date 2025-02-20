## DESCRIPTION

*v.habitat.dem* calculates DEM and solar derived characteristics of
habitat vector polygons. The user must specify the input **elevation
raster** map, a **habitat vector** map with a **numeric unique ID**
column and a **prefix** used for all results.

A preliminary visual delineation of habitats based upon digital
orthophotos is a common task for an ecologist before fieldwork.
Ecological site conditions of habitats are often influenced amongst
others by terrain forms, solar irradiance and irradiation.
*v.habitat.dem* gives some DEM derived characteristics for a quick
validation of the preliminary visual habitat delineation.

## NOTES

The location has to be in a projected coordination system. Before
running *v.habitat.dem* the region has to be aligned to the **elevation
raster** map and the **habitat vector** map by *g.region*. During
calculations, especially for solar characteristics, the region will be
extended by a user input (default 5.000). The results are as good as the
DEM quality and resolution is.

### Terrain characteristics

**Slope** and **aspect** are calculated by *r.slope.aspect*.

The **slope** output raster map contains slope values, stated in degrees
of inclination from the horizontal.  
The **aspect** output raster map indicates the direction that slopes are
facing. The aspect categories represent the number degrees of east.

**Accumulation**, **drainage direction** and **topographic index** are
calculated by *r.watershed*. The flag **-a** (use positive flow
accumulation even for likely underestimates) is used as default.

The **accumulation** map contains the absolute value of each cell in
this output map and is the amount of overland flow that traverses the
cell. This value will be the number of upland cells plus one if no
overland flow map is given.  
The **drainage direction** map contains drainage direction. Provides the
"aspect" for each cell measured CCW from East.  
The **topographic index** raster map contains topographic index TCI and
is computed as `ln(α / tan(β))` where α a is the cumulativeupslope area
draining through a point per unit contour length and `tan(β)` is the
local slope angle. The TCI reflects the tendency of water to accumulate
at any point in the catchment and the tendency for gravitaional forces
to move that water downslope. This value will be negative if `α / tan(β)
< 1`.

Terrain forms are calculated by *r.geomorphon*.

Geomorphon is a new concept of presentation and analysis of terrain
forms using machine vision approach. This concept utilises 8-tuple
pattern of the visibility neighbourhood and breaks well known limitation
of standard calculus approach where all terrain forms cannot be detected
in a single window size. The pattern arises from a comparison of a focus
pixel with its eight neighbours starting from the one located to the
east and continuing counterclockwise producing a ternary operator. All
options in the *r.geomorphon*-calculation are set to default (**skip =
0**, **search = 3**, **flat = 1**, **dist = 0**) where **search**
determines the length on the geodesic distances in all eight directions
where line-of-sight is calculated, **skip** determines length on the
geodesic distances at the beginning of calculation all eight directions
where line-of-sight is yet calculated, **flat** defines the difference
(in degrees) between zenith and nadir line-of-sight which indicate flat
direction and **dist** determines \> flat distance.

The most common terrain forms calculated by *r.geomorphon* are:

  - flat
  - summit
  - ridge
  - shoulder
  - spur
  - slope
  - hollow
  - footslope
  - valley
  - depression

The LS factor

The LS is the slope length-gradient factor. The LS factor represents a
ratio of soil loss under given conditions to that at a site with the
"standard" slope steepness of 9% and slope length of 22.13m. The steeper
and longer the slope, the higher the risk for erosion.

The LS factor is calculated accordingly Neteler & Mitasova 2008 in
*r.mapcalc* with flow accumulation of *r.flow* and slope of
*r.slope.aspect*

```sh
  1.4 * exp(flow_accumulation * resolution / 22.1, 0.4) * exp(sin(slope) 0.09, 1.2)
 
```

The colors of the LS factor map are set to:

  - 0 white
  - 3 yellow
  - 6 orange
  - 10 red
  - 50 magenta
  - 100 violet

### Terrain characteristics uploaded to the habitat vector attribute table per polygon

  - **DEM altitude**: minimum, maximum, range, average, median
  - **slope**: minimum, maximum, range, average, median
  - **aspect**: minimum, maximum, range, average, median
  - **geomorphons**: absolute area of flat, summit, ridge, shoulder,
    spur, slope, hollow, footslope, valley, depression

Additionally the mutual occurrence by *r.coin* of unique habitat ID and
geomorphons in percent of the row is printed to the output.

### Simple check of terrain characteristics

Simple checks regarding aspect and slope per unique habitat ID are
evaluated and marked in the attribute table as follow:

  - **simple check regarding aspect range:**
  - aspect range 100-200 \*
  - aspect range 201-300 \*\*
  - aspect range ≥ 300 \*\*\*
  - **simple checks regarding aspect range and slope median:**
  - aspect range 100-200 and median slope \< 5 \*
  - aspect range 201-300 and median slope \< 5 \*\*
  - aspect range ≥ 300 and median slope \< 5 \*\*\*

These simple checks may indicate reconsidering of some preliminary
visual habitat delineations.

### Solar characteristics

The solar characterstics (direct sunlight / shadows caused by terrain
for a certain day in the year) are calculated by *r.sun.hourly* based
upon *r.sun*. The **-b**-flag is used to create binary rasters instead
of irradiation rasters. The user can define start time of interval, end
time of interval, time step for running *r.sun*, number of day of the
year and the year. As default is set summer solstice (21st June 2014,
8:00-18:00, 1 hour time step).

The results of the *r.sun.hourly*-analysis are automatically registered
into a temporal database. The space time raster dataset can be easily
animated in the *g.gui.animation*-tool.

## EXAMPLE

```sh
# align region to DEM and habitat vector
g.region -a raster=DEM vector=myhabitats align=DEM

# run v.habitat.dem
v.habitat.dem elevation=DEM vector=myhabitats column=Id prefix=a dir=C:\wd

# do r.null to the r.sun.hourly output to get maps without direct beam
r.null map=a_beam_rad_08.00 setnull=1
[...]
r.null map=a_beam_rad_18.00 setnull=1

# animate the r.sun.hourly output by the g.gui.animation-tool
g.gui.animation strds=a_beam_rad
```

## DEPENDENCIES

  - r.geomorphon
  - r.sun.hourly (addon)

## SEE ALSO

*[g.gui.animation](https://grass.osgeo.org/grass-stable/manuals/g.gui.animation.html)
[g.region](https://grass.osgeo.org/grass-stable/manuals/g.region.html),
[r.coin](https://grass.osgeo.org/grass-stable/manuals/r.coin.html),
[r.geomorphon](https://grass.osgeo.org/grass-stable/manuals/r.geomorphon.html),
[r.mapcalc](https://grass.osgeo.org/grass-stable/manuals/r.mapcalc.html),
[r.slope.aspect](https://grass.osgeo.org/grass-stable/manuals/r.slope.aspect.html),
[r.sun](https://grass.osgeo.org/grass-stable/manuals/r.sun.html),
[r.sun.hourly](r.sun.hourly.md) (addon),
[r.stats](https://grass.osgeo.org/grass-stable/manuals/r.stats.html),
[r.watershed](https://grass.osgeo.org/grass-stable/manuals/r.watershed.html),
[v.rast.stats](https://grass.osgeo.org/grass-stable/manuals/v.rast.stats.html),
[v.to.rast](https://grass.osgeo.org/grass-stable/manuals/v.to.rast.html)*

## REFERENCES

Neteler, M. and Mitasova, H. 2008. [Open Source GIS: A GRASS GIS
Approach](https://grassbook.org/). Third Edition. Springer.

## AUTHOR

Helmut Kudrnovsky
