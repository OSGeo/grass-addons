## DESCRIPTION

*r.diversity* calculates selected diversity indices by calling various
*r.li* commands.

This script uses the Pielou, Renyi, Shannon and Simpson indices. The
output is a map for each index.

## NOTES

The user does not need to create a "conf" file with *r.li.setup* because
this file will be created automatically by the script.  
In **size** option it is possible use more values: the user can set more
values with comma (,) and a range with minus (-).  
If you calculate Renyi entropy remember to add the **alpha** option.
Alpha option support single and multi values but not a range.  
If the input raster contains NULL value cells, *r.diversity* returns -1
for these cells.  
If the user wants to keep NULL values instead, run subsequently on the
resulting map:  

```sh
r.null map=my_map setnull=-1
```

## EXAMPLES

To calculate the set of indices from a NDVI map, with a moving window of
3 x 3 pixel, run:

```sh
r.diversity input=ndvi_map prefix=diversity alpha=0.5
```

To calculate the set of indices from a NDVI map, with a moving window of
7 x 7 pixel, run:

```sh
r.diversity input=ndvi_map prefix=diversity alpha=0.5 size=7
```

To calculate only Pielou and Simpson indices from a NDVI map, with
several moving window (3 x 3, 5 x 5, 7 x 7, 9 x 9), run:

```sh
r.diversity input=ndvi_map prefix=diversity size=3-9 method=pielou,simpson
```

To calculate all methods excluding Pielou from a NDVI map, with two
moving window (3 x 3, 9 x 9), run:

```sh
r.diversity input=ndvi_map prefix=diversity size=3,9 exclude=pielou alpha=3
```

## SEE ALSO

*[r.li](https://grass.osgeo.org/grass-stable/manuals/r.li.html),
[r.li.pielou](https://grass.osgeo.org/grass-stable/manuals/r.li.pielou.html),
[r.li.renyi](https://grass.osgeo.org/grass-stable/manuals/r.li.renyi.html),
[r.li.shannon](https://grass.osgeo.org/grass-stable/manuals/r.li.shannon.html),
[r.li.simpson](https://grass.osgeo.org/grass-stable/manuals/r.li.simpson.html)*

## AUTHORS

Luca Delucchi and Duccio Rocchini, Fondazione E. Mach (Italy)
