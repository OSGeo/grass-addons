## DESCRIPTION

*t.stac.catalog* is a tool for exploring SpatioTemporal Asset Catalogs
metadata from a STAC API. A list of STAC API and Catalogs can be found
at <https://stacindex.org/catalogs>. The tool is based on the PySTAC
library and provides a set of modules for working with STAC APIs.

## REQUIREMENTS

- [PySTAC\_Client
    (0.8.3)](https://pystac-client.readthedocs.io/en/stable/)

## EXAMPLES

Get the catalog metadata from a STAC API.

### STAC Catalog JSON metadata

```sh
t.stac.catalog url="https://earth-search.aws.element84.com/v1/"
```

GRASS Jupyter Notebooks can be used to visualize the catalog metadata.

```python
from grass import gs
catalog = gs.parse_command("t.stac.catalog", url="https://earth-search.aws.element84.com/v1/", flags="p")
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
t.stac.catalog url=https://earth-search.aws.element84.com/v1/ format=plain -b

---------------------------------------------------------------------------
Catalog: Earth Search by Element 84
---------------------------------------------------------------------------
Client Id: earth-search-aws
Client Description: A STAC API of public datasets on AWS
Client STAC Extensions: []
Client catalog_type: ABSOLUTE_PUBLISHED
---------------------------------------------------------------------------
Collections: 9
---------------------------------------------------------------------------
Collection Id | Collection Title
---------------------------------------------------------------------------
sentinel-2-pre-c1-l2a: Sentinel-2 Pre-Collection 1 Level-2A
cop-dem-glo-30: Copernicus DEM GLO-30
naip: NAIP: National Agriculture Imagery Program
cop-dem-glo-90: Copernicus DEM GLO-90
landsat-c2-l2: Landsat Collection 2 Level-2
sentinel-2-l2a: Sentinel-2 Level-2A
sentinel-2-l1c: Sentinel-2 Level-1C
sentinel-2-c1-l2a: Sentinel-2 Collection 1 Level-2A
sentinel-1-grd: Sentinel-1 Level-1C Ground Range Detected (GRD)
---------------------------------------------------------------------------
```

### Basic STAC catalog metadata

```sh
t.stac.catalog url=https://earth-search.aws.element84.com/v1/ format=plain

---------------------------------------------------------------------------
Catalog: Earth Search by Element 84
---------------------------------------------------------------------------
Client Id: earth-search-aws
Client Description: A STAC API of public datasets on AWS
Client STAC Extensions: []
Client catalog_type: ABSOLUTE_PUBLISHED
---------------------------------------------------------------------------
Collections: 9
---------------------------------------------------------------------------
Collection: Sentinel-2 Pre-Collection 1 Level-2A
---------------------------------------------------------------------------
Collection Id: sentinel-2-pre-c1-l2a
Sentinel-2 Pre-Collection 1 Level-2A (baseline < 05.00), with data and metadata matching collection sentinel-2-c1-l2a
Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2015-06-27T10:25:31.456000Z', None]]}}
License: proprietary
---------------------------------------------------------------------------
---------------------------------------------------------------------------
Collection: Copernicus DEM GLO-30
---------------------------------------------------------------------------
Collection Id: cop-dem-glo-30
The Copernicus DEM is a Digital Surface Model (DSM) which represents the surface of the Earth including buildings, infrastructure and vegetation. GLO-30 Public provides limited worldwide coverage at 30 meters because a small subset of tiles covering specific countries are not yet released to the public by the Copernicus Programme.
Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2021-04-22T00:00:00Z', '2021-04-22T00:00:00Z']]}}
License: proprietary
---------------------------------------------------------------------------
...
Extent: {'spatial': {'bbox': [[-180, -90, 180, 90]]}, 'temporal': {'interval': [['2014-10-10T00:28:21Z', None]]}}
License: proprietary
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
[t.stac.collection](https://grass.osgeo.org/grass-stable/manuals/t.stac.collection.html),
[t.stac.item](https://grass.osgeo.org/grass-stable/manuals/t.stac.item)*

[GRASS GIS Wiki: temporal data
processing](https://grasswiki.osgeo.org/wiki/Temporal_data_processing)

## AUTHORS

Corey T. White  

## Sponsors

- [OpenPlains Inc.](https://openplains.com)
- [NCSU GeoForAll Lab](https://geospatial.ncsu.edu/geoforall/)

Center for Geospatial Analytics at North Carolina State University
