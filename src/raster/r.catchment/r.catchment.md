## DESCRIPTION

*r.catchment* is a module that facilitates modeling "catchments" around
point locations according to a walking cost function. The module is
particularly aimed at "Site Catchment Analysis" for archaeology, but
could be potentially useful in any number of applications where
delimiting an area based on walking-costs is desirable. Although
defining a catchment based on a threshold in walking-costs (or time) can
be undertaken using *r.walk* or *r.cost* alone, this addon module allows
the user to enter a pre-determined square meterage (option **area**) for
the resultant catchment, which is a different approach. This is useful
for applications where the user wants to make a catchment of a
particular size (e.g., certain number of square meters needed for farmed
fields), and doesn't want to spend time via trial and error
experimenting with different cost radii.

Additionally, this module allows the user to enter a slope threshold
(option **sigma**), which will mask out areas of higher slope. This is
useful for delimiting catchments that are of generally flat land (e.g.,
areas where agriculture are likely).

Optionally, you can iteratively loop through a series of input starting
points, and create catchments for each point. You can also opt to save
the cost map produced by r.walk for each input point. This can be a
useful timesaver for the creation of many cost maps and/or catchment
maps with minimal manual repetition.

Important: The user must run **g.region** first to make sure that the
region boundaries and the resolution match the input elevation map.

### Options and flags:

*r.catchment* requires an input elevation map, **elevation** , and an
input vector points map of starting locations, **start\_points**.
**area** is also requited, which is an integer value for the size of the
desired catchment (in the map units of the defined location/region). The
final required parameter is **map\_val** , which is the integer value to
write to the areas defined as part of the catchment in the output map,
**buffer**. The optional value, **sigma** is the slope threshold cut off
value. Slopes above **sigma** will be masked out during the
determination of the catchment configuration. The optional value
**name\_column** is to be used in conjunction with the **-i** flag (see
below). There are three native flags for *r.catchment*. **-c** allows
you to keep the interim cost surface maps made. **-l** allows you to
show a list of the costv alues in that cost map, along with the size of
the catchments they delineate. **-i** enable "iterative" mode. Here, the
module will loop through all the points in the input vector file
**start\_points**, calculating a cost map and catchment map around each
point. If **name\_column** is specified, then each output map will
contain the text value in that column as an prefix. Otherwise, the cat
number for each vector point will be used. All other flags and options
are inherited from *r.walk* (see the
[r.walk](https://grass.osgeo.org/grass-stable/manuals/r.walk.html) help
page for more information on these).

## NOTES

The module will attempt to find the cost radius that defines an area
close to the value of **area**, but em will likely slightly overestimate
the catchment size. The module will display the actual area of the
defined catchment in the Command Output. By default, *r.catchment* will
create a **friction** map of value 0, which, when input into *r.walk*
will yield a cost surface based on walking times only. The user may
optionally create a **friction** map, however, and, if used, r.walk will
consider these costs this as well when determining the cost surface used
to determine the catchment. The input **start\_points** map should be a
vector points map. If the file contains other types of features (areas,
lines, centroids), these will be ignored. If you desire, a start points
map could be manually digitized (with *v.digit*) over topographic or
cultural features, or could be created as a series of random points
(with *r.random* or *v.random*). Unless the **-i** flag is used, in the
case of multiple input points, the routine will attempt to equally
divide the area (**area**) between all input points tod etermine
catchments for each point. The total area of all these catchments will
sum (close) to **area**. If two input points are close, their catchments
may overlap. In this case, the routine will "meld" the two, and the
melded catchment will till be of an area close to **area**. If truly
overlapping catchments are desired, then the routine should be run with
the **-i** flag. This will create completely independent catchments
around each input point.

## EXAMPLES

Delimit a catchment of 5,000,000 square meters around a single start
point, ignoring areas of slope \> 15 degrees:  

```sh
r.catchment elevation=DEM10m start_points=site buffer=test_catchment
sigma=15 area=5000000 map_val=1
```

## SEE ALSO

*[r.walk](https://grass.osgeo.org/grass-stable/manuals/r.walk.html),
[r.cost](https://grass.osgeo.org/grass-stable/manuals/r.cost.html)*

## AUTHOR

Isaac Ullah

Updated for GRASS 8, 02, Feb. 2023.
