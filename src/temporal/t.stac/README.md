# (In-Development) t.stac.import

## Description

**t.stac.import** utilizes the
[pystac-client (v0.5.1)](https://github.com/stac-utils/pystac-client) to search
STAC APIs and import and import items into GRASS GIS.

### Item Search Parameters

[Offical Docs](https://pystac-client.readthedocs.io/en/stable/api.html#item-search)

**method** – The HTTP method to use when making a request to the service. This
must be either "GET", "POST", or None. If None, this will default to "POST".
If a "POST" request receives a 405 status for the response, it
will automatically retry with "GET" for all subsequent requests.

**max_items** – The maximum number of items to return from the search, even if
there are more matching results. This client to limit the total number of Items
returned from the items(), item_collections(), and items_as_dicts methods().
The client will continue to request pages of items until the number of max
items is reached. This parameter defaults to 100. Setting this to None will
allow iteration over a possibly very large number of results.

**limit** – A recommendation to the service as to the number of items to return
per page of results. Defaults to 100.

**ids** – List of one or more Item ids to filter on.

**collections** – List of one or more Collection IDs or pystac.Collection
instances. Only Items in one of the provided Collections will be searched.

**bbox** – A list, tuple, or iterator representing a bounding box of 2D
or 3D coordinates. Results will be filtered to only those intersecting the
bounding box.

**intersects** – A string or dictionary representing a GeoJSON geometry,
or an object that implements a ``__geo_interface__`` property, as supported
by several libraries including Shapely, ArcPy, PySAL, and geojson.
Results filtered to only those intersecting the geometry.

**datetime –**
Either a single datetime or datetime range used to filter results. You may
express a single datetime using a datetime.datetime instance, a
RFC 3339-compliant timestamp, or a simple date string (see below).
Instances of datetime.datetime may be either timezone aware or unaware.
Timezone aware instances will be converted to a UTC timestamp before being
passed to the endpoint. Timezone unaware instances are assumed to represent
UTC timestamps. You may represent a datetime range using a "/" separated
string as described in the spec, or a list, tuple, or iterator of 2 timestamps
or datetime instances. For open-ended ranges, use either".."
('2020-01-01:00:00:00Z/..', ['2020-01-01:00:00:00Z', '..']) or
a value of None (['2020-01-01:00:00:00Z', None]).

If using a simple date string, the datetime can be specified in YYYY-mm-dd
format, optionally truncating to YYYY-mm or just YYYY. Simple date strings
will be expanded to include the entire time period, for example:

* 2017 expands to 2017-01-01T00:00:00Z/2017-12-31T23:59:59Z
* 2017-06 expands to 2017-06-01T00:00:00Z/2017-06-30T23:59:59Z
* 2017-06-10 expands to 2017-06-10T00:00:00Z/2017-06-10T23:59:59Z

If used in a range, the end of the range expands to
the end of that day/month/year, for example:

* 2017/2018 expands to 2017-01-01T00:00:00Z/2018-12-31T23:59:59Z
* 2017-06/2017-07 expands to 2017-06-01T00:00:00Z/2017-07-31T23:59:59Z
* 2017-06-10/2017-06-11 expands to 2017-06-10T00:00:00Z/2017-06-11T23:59:59Z

**query** – List or JSON of query parameters as per the STAC API query extension

**filter** – JSON of query parameters as per the STAC API filter extension

**filter_lang** – Language variant used in the filter body. If filter is a
dictionary or not provided, defaults to ‘cql2-json’. If filter is a string,
defaults to cql2-text.

**sortby** – A single field or list of fields to sort the response by

**fields** – A list of fields to include in the response.
Note this may result in invalid STAC objects, as they may not have required
fields. Use items_as_dicts to avoid object unmarshalling errors.

### Dependancies

* [pystac-client (v0.5.1)](https://github.com/stac-utils/pystac-client)

#### Optional Query

* [STAC API - Query Extension Specification](https://github.com/stac-api-extensions/query)

### S3 and GCS Requester Pays Support

* [GDAL Docs](https://gdal.org/user/virtual_file_systems.html#introduction)
* [STAC API - S3 Requester Pays](https://gdal.org/user/virtual_file_systems.html#vsis3-aws-s3-files)
* [STAC API - GCS Requester Pays](https://gdal.org/user/virtual_file_systems.html#vsigs-google-cloud-storage-files)

## Basic Usage

1. Check the STAC API for the available collections.

    ```bash
    t.stac.import -c urlhttps://earth-search.aws.element84.com/v1/
    ```

2. Search for items in the collection.

    ```bash
    t.stac.import -i url=https://earth-search.aws.element84.com/v1/
    collections=sentinel-2-l2a
    ```

3. Import (dry-run) the items into GRASS GIS.

    ```bash
    t.stac.import -d url=https://earth-search.aws.element84.com/v1/
    collections=sentinel-2-l2a
    ```
