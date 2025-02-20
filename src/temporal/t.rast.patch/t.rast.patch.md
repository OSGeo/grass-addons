## DESCRIPTION

This module patches raster maps that have gaps in time with subsequent
maps (within a space time raster dataset) using *r.patch* or
**r.buildvrt**. Hence it is a wrapper for those two modules in the
temporal domain.

By default *r.patch* is used to create a patched raster map. Especially
for temporary data, using **r.buildvrt** for patching can be
advantageous with regards to processing time and storage space.
**r.buildvrt** creates a virtual raser map and is used when the
**v-flag** is given. The **v-flag** excludes the **z-flag** (using zero
(0) for transperancy) and **s-flag (do not create color and category
files)**.

The input of this module is a single space time raster dataset, the
output is a single raster map layer. A subset of the input space time
raster dataset can be selected using the **where** option. The sorting
of the raster map layer can be set using the **sort** option. Be aware
that the sorting of the maps significantly influences the result of the
patch. By default the maps are sorted by **desc** by the *start\_time*
so that the newest raster map is the first input map in
**r.patch**/**r.buildvrt**.

Please note that the color table of the first input raster is used for
the resulting map when the **v-flag** is used. Values in the resulting
raster map that exeed the range of that first raster map will then be
rendered on the screen like no data. In that case, please update the
color table or the resulting map with **r.colors**

*t.rast.patch* is a simple wrapper for the raster module **r.patch** or
**r.buildvrt**.

## EXAMPLE

The example uses the North Carolina extra time series of MODIS Land
Surface Temperature maps
([download](https://grass.osgeo.org/download/data/)). (The mapset has to
be unzip in one of the North Carolina locations.)

Patching the MODIS Land Surface Temperature for 2016 (filling missing
pixels by subsequent maps in the time series):

```sh
t.rast.patch input=LST_Day_monthly@modis_lst output=LST_Day_patched_2016 \
  where="start_time >= '2016-01' and start_time <= '2016-12'"
r.info LST_Day_patched_2016
```

Patching the MODIS Land Surface Temperature for 2016 (filling missing
pixels by subsequent maps in the time series) using a virtual mosaic
(**r.buildvrt**):

```sh
t.rast.patch -v input=LST_Day_monthly@modis_lst output=LST_Day_patched_2016_vrt \
  where="start_time >= '2016-01' and start_time <= '2016-12'"
# Assign a new color table that covers the entire range of the resulting map
r.colors map=LST_Day_patched_2016_vrt color=grey
r.info LST_Day_patched_2016_vrt
```

## SEE ALSO

*[r.buildvrt](https://grass.osgeo.org/grass-stable/manuals/r.buildvrt.html),
[r.patch](https://grass.osgeo.org/grass-stable/manuals/r.patch.html),
[t.rast.series](https://grass.osgeo.org/grass-stable/manuals/t.rast.series.html),
[t.create](https://grass.osgeo.org/grass-stable/manuals/t.create.html),
[t.info](https://grass.osgeo.org/grass-stable/manuals/t.info.html),
[t.merge](https://grass.osgeo.org/grass-stable/manuals/t.merge.html)*

[Temporal data processing
Wiki](https://grasswiki.osgeo.org/wiki/Temporal_data_processing)

## AUTHOR

Anika Bettge, mundialis GmbH & Co. KG
