## DESCRIPTION

The purpose of *r.windfetch* is to compute wind fetch, which is the
length of water over which winds blow without obstruction. Fetch is an
important feature in wave modeling for waves created by wind.

Input is a binary raster map **input** where land is 1 and 0 is water.
To compute fetch for certain point(s), user provides either the
coordinates with the **coordinates** parameter or a points vector map
with **points** parameter. Output is formatted with **format** parameter
either as JSON or CSV and can be printed to a file (**output\_file**) or
to standard output.

## NOTES

Wind fetch is computed for specific directions, determined by parameters
**direction** and **step**. Direction angle is in degrees
counterclockwise from the East. For example, for `direction=45` and
`step=90`, *r.windfetch* computes fetch for directions 45, 135, 225, and
315 (NE, NW, SW, SE). By default wind fetch for each direction is
averaged from multiple directions around it. The number of minor
directions from which the main direction is computed is specified with
parameter **minor\_directions**. The step between the minor directions
is given in **minor\_step** and is in degrees.

## EXAMPLE

Compute wind fetch on a lake edge with default parameters:

```sh
r.mapcalc "land = if (isnull(lakes), 1, 0)"
r.windfetch input=land format=csv coordinates=635659,223234
```

[![image-alt](r_windfetch.png)](r_windfetch.png)  
*Figure: Wind fetch for a selected point, visualized in a polar plot.*

## SEE ALSO

*[r.horizon](https://grass.osgeo.org/grass-stable/manuals/r.horizon.html)*
is used for computing distances.

## AUTHORS

Anna Petrasova, [NCSU GeoForAll
Lab](https://geospatial.ncsu.edu/geoforall/). This addon was developed
with funding from [NSF Award
\#2322073](https://www.nsf.gov/awardsearch/showAward?AWD_ID=2322073),
granted to Natrx, Inc.
