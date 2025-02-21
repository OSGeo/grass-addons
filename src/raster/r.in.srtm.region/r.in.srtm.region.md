## DESCRIPTION

*r.in.srtm.region* imports all SRTM tiles covering the current region or
region extents given with **region** into GRASS, patches the tiles
together and optionally interpolates holes for SRTM V2.1. The SRTM V003
products are already void-filled.

*r.in.srtm.region* downloads ([SRTM product
description](https://lpdaac.usgs.gov/documents/179/SRTM_User_Guide_V3.pdf))

- SRTMGL1 V003 tiles at 1 arc second (about 30 meters) resolution,
    void-filled from:  
    <https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL1.003/2000.02.11/>
- SRTMGL3 V003 tiles at 3 arc seconds (about 90 meters) resolution,
    void-filled from:  
    <https://e4ftl01.cr.usgs.gov/MEASURES/SRTMGL3.003/2000.02.11/>
- SRTM V2.1 tiles at 3 arc second (about 90 meters) resolution from:
    [http://dds.cr.usgs.gov/srtm/](http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/)
- or, optionally *r.in.srtm.region* uses a local folder with
    previously downloaded SRTM data files if the **local** option is
    given.

Importantly, for the SRTM tiles download a user registration is needed
at <https://urs.earthdata.nasa.gov/users/new>

In the user profile, two specific applications must be approved in the
"My application" tab:

- "LP DAAC Data Pool" application, and
- "Earthdata Search" application.

## EXAMPLE

Import of SRTMGL1 V003 (1 arc seconds \~ 30m) covering the current
computational region:

```sh
# run in LatLong location - Sicily East, Italy
g.region n=39 s=37 w=14 e=16 res=0:00:01 -p

# use own credentials here
r.in.srtm.region -1 user="my_nasa_user" password="my_nasa_pw" output=srtm_sicily_1arc memory=2000
r.univar srtm_sicily_1arc
```

[![image-alt](r_in_srtm_region_etna.png)](r_in_srtm_region_etna.png)  
*Figure: Eta volcano (Sicily, Italy) shown in NVIZ*

## SEE ALSO

*[r.in.srtm](https://grass.osgeo.org/grass-stable/manuals/r.in.srtm.html),
[r.in.nasadem](r.in.nasadem.md) (addon)*

The [Shuttle Radar Topography Mission](http://www2.jpl.nasa.gov/srtm/)
homepage at NASA's JPL (see also [MEaSUREs Data Product Table -
SRTM](https://lpdaac.usgs.gov/product_search/?collections=MEaSUREs+SRTM&status=Operational&view=list)).

The [SRTM v3
documentation](https://lpdaac.usgs.gov/sites/default/files/public/measures/docs/NASA_SRTM_V3.pdf).

[SRTMGL1: NASA Shuttle Radar Topography Mission Global 1 arc second
V003](https://lpdaac.usgs.gov/products/srtmgl1v003/)

NASA JPL. (2013). *NASA Shuttle Radar Topography Mission Global 1 arc
second.* NASA LP DAAC.
<https://doi.org/10.5067/MEaSUREs/SRTM/SRTMGL1.003>

## REFERENCES

M. Neteler, 2005. [SRTM and VMAP0 data in OGR and
GRASS.](https://grass.osgeo.org/newsletter/GRASSNews_vol3.pdf) *[GRASS
Newsletter](https://grass.osgeo.org/newsletter/)*, Vol.3, pp. 2-6, June
2005. ISSN 1614-8746.

## AUTHORS

Markus Metz  
Reprojection support: Anika Bettge, mundialis
