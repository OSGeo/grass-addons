## DESCRIPTION

*t.stac.item* is a tool for exploring and importing SpatioTemporal Asset
Catalog item metadata and assets into GRASS GIS. The tool is based on
the [PySTAC\_Client
(0.8)](https://pystac-client.readthedocs.io/en/stable/) library and
allows you to search items in a STAC Catalog. The search can be done by
specifying the item ID, collection ID, datatime or by using a search
query. The full list of search parameters and documentation can be found
at [PySTAC\_Client
ItemSearch](https://pystac-client.readthedocs.io/en/stable/api.html#item-search).

## NOTES

The *t.stac.item* tool is part of the
[t.stac](https://grass.osgeo.org/grass-stable/manuals/t.stac.html)
temporal data processing framework. The tool requries that the data
provider has implement the STAC API and conforms to *Item Search*
specification.

## REQUIREMENTS

- [PySTAC
    (1.10.x)](https://pystac.readthedocs.io/en/stable/installation.html)
- [PySTAC\_Client
    (0.8)](https://pystac-client.readthedocs.io/en/stable/)
- tqdm (4.66.x)
- numpy (1.26.x)

## EXAMPLES

### Get the item metadata from a STAC API

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
    t.stac.collection url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a"
    t.stac.item -i url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

### Get the asset metadata from a STAC API

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
    t.stac.collection url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a"
    t.stac.item -a url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

### Use datetime filter

```sh
    t.stac.item url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" datetime=2017-06-10/2017-06-11
```

### Use query option

```sh
    t.stac.item url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" query='{"eo:cloud_cover":{"lt":10}}'
```

To read more about `query` option please look at [pystac_client documentation](https://pystac-client.readthedocs.io/en/stable/tutorials/cql2-filter.html)

### Dpwnload the asset from a STAC API

```sh
    t.stac.item -d url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

### Download and import filtering by asset

```sh
    t.stac.item url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" query='{"eo:cloud_cover":{"lt":10}}' asset=red,nir
```

## SEE ALSO

*Requirements
[t.stac.collection](https://grass.osgeo.org/grass-stable/manuals/t.stac.collection.html),
[t.stac.catalog](https://grass.osgeo.org/grass-stable/manuals/t.stac.catalog.html)*

[GRASS GIS Wiki: temporal data
processing](https://grasswiki.osgeo.org/wiki/Temporal_data_processing)

## AUTHORS

Corey T. White

## Sponsors

- [OpenPlains Inc.](https://openplains.com)
- [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)

Center for Geospatial Analytics at North Carolina State University
