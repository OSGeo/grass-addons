## DESCRIPTION

*t.stac.collection* is a tool for exploring SpatioTemporal Asset Catalog
(STAC) collection metadata. The tool is based on the [PySTAC\_Client
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

### Get the item metadata from a STAC API.

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
    t.stac.collection url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a"
    t.stac.item -i url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

### Get the asset metadata from a STAC API.

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
    t.stac.collection url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a"
    t.stac.item -a url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

### Dpwnload the asset from a STAC API.

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
    t.stac.collection url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a"
    t.stac.item -d url="https://earth-search.aws.element84.com/v1/" collection_id="sentinel-2-l2a" item_id="S2B_36QWD_20220301_0_L2A"
```

GRASS Jupyter Notebooks can be used to visualize the catalog metadata.

```sh
    from grass import gs
    catalog = gs.parse_command('t.stac.catalog', url="https://earth-search.aws.element84.com/v1/")

    print(catalog)

    # Output
    {'conformsTo': ['https://api.stacspec.org/v1.0.0/core',
                'https://api.stacspec.org/v1.0.0/collections',
                'https://api.stacspec.org/v1.0.0/ogcapi-features',
                'https://api.stacspec.org/v1.0.0/item-search',
                'https://api.stacspec.org/v1.0.0/ogcapi-features#fields',
                'https://api.stacspec.org/v1.0.0/ogcapi-features#sort',
                'https://api.stacspec.org/v1.0.0/ogcapi-features#query',
                'https://api.stacspec.org/v1.0.0/item-search#fields',
                'https://api.stacspec.org/v1.0.0/item-search#sort',
                'https://api.stacspec.org/v1.0.0/item-search#query',
                'https://api.stacspec.org/v0.3.0/aggregation',
                'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core',
                'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30',
                'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson'],
 'description': 'A STAC API of public datasets on AWS',
 'id': 'earth-search-aws',
 'stac_version': '1.0.0',
 'title': 'Earth Search by Element 84',
 'type': 'Catalog'}
```

### STAC Catalog plain text metadata

```sh
t.stac.catalog url=https://earth-search.aws.element84.com/v1/ format=plain

# Output
    Client Id: earth-search-aws
    Client Title: Earth Search by Element 84
    Client Description: A STAC API of public datasets on AWS
    Client STAC Extensions: []
    Client Extra Fields: {'type': 'Catalog', 'conformsTo': ['https://api.stacspec.org/v1.0.0/core', 'https://api.stacspec.org/v1.0.0/collections', 'https://api.stacspec.org/v1.0.0/ogcapi-features', 'https://api.stacspec.org/v1.0.0/item-search', 'https://api.stacspec.org/v1.0.0/ogcapi-features#fields', 'https://api.stacspec.org/v1.0.0/ogcapi-features#sort', 'https://api.stacspec.org/v1.0.0/ogcapi-features#query', 'https://api.stacspec.org/v1.0.0/item-search#fields', 'https://api.stacspec.org/v1.0.0/item-search#sort', 'https://api.stacspec.org/v1.0.0/item-search#query', 'https://api.stacspec.org/v0.3.0/aggregation', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson']}
    Client catalog_type: ABSOLUTE_PUBLISHED
    ---------------------------------------------------------------------------
    Collections: 9
    sentinel-2-pre-c1-l2a: Sentinel-2 Pre-Collection 1 Level-2A
    Sentinel-2 Pre-Collection 1 Level-2A (baseline < 05.00), with data and metadata matching collection sentinel-2-c1-l2a
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2015-06-27T10:25:31.456000Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
    cop-dem-glo-30: Copernicus DEM GLO-30
    The Copernicus DEM is a Digital Surface Model (DSM) which represents the surface of the Earth including buildings, infrastructure and vegetation. GLO-30 Public provides limited worldwide coverage at 30 meters because a small subset of tiles covering specific countries are not yet released to the public by the Copernicus Programme.
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2021-04-22T00:00:00Z', '2021-04-22T00:00:00Z']]}}
    License: proprietary
    ---------------------------------------------------------------------------
    naip: NAIP: National Agriculture Imagery Program
    The [National Agriculture Imagery Program](https://www.fsa.usda.gov/programs-and-services/aerial-photography/imagery-programs/naip-imagery/) (NAIP) provides U.S.-wide, high-resolution aerial imagery, with four spectral bands (R, G, B, IR).  NAIP is administered by the [Aerial Field Photography Office](https://www.fsa.usda.gov/programs-and-services/aerial-photography/) (AFPO) within the [US Department of Agriculture](https://www.usda.gov/) (USDA).  Data are captured at least once every three years for each state.  This dataset represents NAIP data from 2010-present, in [cloud-optimized GeoTIFF](https://www.cogeo.org/) format.
    Extent: {'spatial': {'bbox': [[-160, 17, -67, 50]]}, 'temporal': {'interval': [['2010-01-01T00:00:00Z', '2022-12-31T00:00:00Z']]}}
    License: proprietary
    ---------------------------------------------------------------------------
    cop-dem-glo-90: Copernicus DEM GLO-90
    The Copernicus DEM is a Digital Surface Model (DSM) which represents the surface of the Earth including buildings, infrastructure and vegetation. GLO-90 provides worldwide coverage at 90 meters.
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2021-04-22T00:00:00Z', '2021-04-22T00:00:00Z']]}}
    License: proprietary
    ---------------------------------------------------------------------------
    landsat-c2-l2: Landsat Collection 2 Level-2
    Atmospherically corrected global Landsat Collection 2 Level-2 data from the Thematic Mapper (TM) onboard Landsat 4 and 5, the Enhanced Thematic Mapper Plus (ETM+) onboard Landsat 7, and the Operational Land Imager (OLI) and Thermal Infrared Sensor (TIRS) onboard Landsat 8 and 9.
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['1982-08-22T00:00:00Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
    sentinel-2-l2a: Sentinel-2 Level-2A
    Global Sentinel-2 data from the Multispectral Instrument (MSI) onboard Sentinel-2
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2015-06-27T10:25:31.456000Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
    sentinel-2-l1c: Sentinel-2 Level-1C
    Global Sentinel-2 data from the Multispectral Instrument (MSI) onboard Sentinel-2
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2015-06-27T10:25:31.456000Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
    sentinel-2-c1-l2a: Sentinel-2 Collection 1 Level-2A
    Sentinel-2 Collection 1 Level-2A, data from the Multispectral Instrument (MSI) onboard Sentinel-2
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2015-06-27T10:25:31.456000Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
    sentinel-1-grd: Sentinel-1 Level-1C Ground Range Detected (GRD)
    Sentinel-1 is a pair of Synthetic Aperture Radar (SAR) imaging satellites launched in 2014 and 2016 by the European Space Agency (ESA). Their 6 day revisit cycle and ability to observe through clouds makes this dataset perfect for sea and land monitoring, emergency response due to environmental disasters, and economic applications. This dataset represents the global Sentinel-1 GRD archive, from beginning to the present, converted to cloud-optimized GeoTIFF format.
    Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2014-10-10T00:28:21Z', None]]}}
    License: proprietary
    ---------------------------------------------------------------------------
```

### Basic STAC catalog metadata

```sh
    t.stac.catalog url=https://earth-search.aws.element84.com/v1/ format=plain -b

    # Output
    Client Id: earth-search-aws
    Client Title: Earth Search by Element 84
    Client Description: A STAC API of public datasets on AWS
    Client STAC Extensions: []
    Client Extra Fields: {'type': 'Catalog', 'conformsTo': ['https://api.stacspec.org/v1.0.0/core', 'https://api.stacspec.org/v1.0.0/collections', 'https://api.stacspec.org/v1.0.0/ogcapi-features', 'https://api.stacspec.org/v1.0.0/item-search', 'https://api.stacspec.org/v1.0.0/ogcapi-features#fields', 'https://api.stacspec.org/v1.0.0/ogcapi-features#sort', 'https://api.stacspec.org/v1.0.0/ogcapi-features#query', 'https://api.stacspec.org/v1.0.0/item-search#fields', 'https://api.stacspec.org/v1.0.0/item-search#sort', 'https://api.stacspec.org/v1.0.0/item-search#query', 'https://api.stacspec.org/v0.3.0/aggregation', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/core', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/oas30', 'http://www.opengis.net/spec/ogcapi-features-1/1.0/conf/geojson']}
    Client catalog_type: ABSOLUTE_PUBLISHED
    ---------------------------------------------------------------------------

```

## AUTHENTICATION

The *t.stac.catalog* tool supports authentication with the STAC API
using the *GDAL's* virtual fie system */vsi/*.

### Basic Authentication

```sh
    t.stac.catalog url="https://earth-search.aws.element84.com/v1/" settings="user:password"
```

### AWS

[AWS
S3](https://gdal.org/user/virtual_file_systems.html#vsis3-aws-s3-files)

### Google Cloud Storage

[Google Cloud
Storage](https://gdal.org/user/virtual_file_systems.html#vsigs-google-cloud-storage-files)

### Microsoft Azure

[Microsoft
Azure](https://gdal.org/user/virtual_file_systems.html#vsiaz-microsoft-azure-blob-files)

### HTTP

[HTTP](https://gdal.org/user/virtual_file_systems.html#vsicurl-http-https-ftp-files-random-access)

## SEE ALSO

*Requirements
[t.stac.item](https://grass.osgeo.org/grass-stable/manuals/t.stac.item)
[t.stac.item](https://grass.osgeo.org/grass-stable/manuals/t.stac.item.html),*

## AUTHORS

Corey T. White  

## Sponsors

  - [OpenPlains Inc.](https://openplains.com)
  - [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)

Center for Geospatial Analytics at North Carolina State University
