## DESCRIPTION

*r.in.nasadem* imports all NASADEM tiles covering the current region or
region extents given with the **region** option into GRASS and patches
the tiles together.

Cited from
<https://lpdaac.usgs.gov/news/release-nasadem-data-products/>:

"NASADEM extends the legacy of the Shuttle Radar Topography Mission
(SRTM) by improving the digital elevation model (DEM) height accuracy
and data coverage as well as providing additional SRTM radar-related
data products. The improvements were achieved by reprocessing the
original SRTM radar signal data and telemetry data with updated
algorithms and auxiliary data not available at the time of the original
SRTM processing."

In total, 14,520 NASADEM tiles are available.

*r.in.nasadem* imports data from
[NASADEM\_HGT.001](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001),
or from a local copy of these data provided with the **local** option.

There are three different layers available in the
[NASADEM\_HGT.001](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001)
product: *hgt*, *num*, and *swb*, each of these layers can be imported
with *r.in.nasadem* with the **layer** option. Importantly, for the
NASADEM tiles download a user registration is needed at
<https://urs.earthdata.nasa.gov/users/new>

In the earthdata user profile, two specific applications must be
approved in the "My application" tab:

- "LP DAAC Data Pool" application, and
- "Earthdata Search" application.

## EXAMPLE

Import of NASADEM\_HGT.001 covering the current computational region:

```sh
# run in LatLong location - Sicily East, Italy
g.region n=39 s=37 w=14 e=16 res=0:00:01 -p

# use own credentials here
r.in.nasadem user="my_nasa_user" password="my_nasa_pw" output=nasadem_sicily_1arc memory=2000
r.univar nasadem_sicily_1arc
```

[![image-alt](r_in_nasadem_etna.jpg)](r_in_nasadem_etna.jpg)  
*Figure: Eta volcano (Sicily, Italy) shown in NVIZ*

## SEE ALSO

*[r.in.srtm](https://grass.osgeo.org/grass-stable/manuals/r.in.srtm.html),
[r.in.srtm.region](r.in.srtm.region.md)*

The [Shuttle Radar Topography Mission](http://www2.jpl.nasa.gov/srtm/)
homepage at NASA's JPL (see also [MEaSUREs Data Product Table -
SRTM](https://lpdaac.usgs.gov/product_search/?collections=MEaSUREs+SRTM&status=Operational&view=list)).

The
[NASADEM\_HGT.001](https://doi.org/10.5067/MEaSUREs/NASADEM/NASADEM_HGT.001)
product page.

## REFERENCES

M. Neteler, 2005. [SRTM and VMAP0 data in OGR and
GRASS.](https://grass.osgeo.org/newsletter/GRASSNews_vol3.pdf) *[GRASS
Newsletter](https://grass.osgeo.org/newsletter/)*, Vol.3, pp. 2-6, June
2005. ISSN 1614-8746.

## AUTHORS

Markus Metz  
Reprojection support: Anika Bettge, mundialis
