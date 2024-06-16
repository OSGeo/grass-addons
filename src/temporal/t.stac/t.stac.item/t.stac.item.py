#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.item
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Get items from a STAC API server
# COPYRIGHT:    (C) 2023-2024 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Downloads and imports data from a STAC API server.
# % keyword: raster
# % keyword: import
# % keyword: STAC
# % keyword: temporal
# %end

# %option
# % key: url
# % type: string
# % description: STAC API Client URL
# % required: yes
# %end

# %option
# % key: collection_id
# % type: string
# % required: yes
# % multiple: no
# % description: Collection Id.
# %end

# %option
# % key: request_method
# % type: string
# % required: no
# % multiple: no
# % options: GET,POST
# % answer: POST
# % description:  The HTTP method to use when making a request to the service.
# % guisection: Request
# %end

# %option
# % key: max_items
# % type: integer
# % description: The maximum number of items to return from the search, even if there are more matching results.
# % multiple: no
# % required: no
# % answer: 10
# % guisection: Request
# %end

# %option
# % key: limit
# % type: integer
# % description: A recommendation to the service as to the number of items to return per page of results. Defaults to 100.
# % multiple: no
# % required: no
# % answer: 100
# % guisection: Request
# %end

# %option
# % key: ids
# % type: string
# % description: List of one or more Item ids to filter on.
# % multiple: no
# % required: no
# % guisection: Query
# %end

# %option
# % key: bbox
# % type: double
# % required: no
# % multiple: yes
# % description: The bounding box of the request in WGS84 (example [-72.5,40.5,-72,41]). (default is current region)
# % guisection: Query
# %end

# %option G_OPT_V_INPUT
# % key: intersects
# % required: no
# % description: Results filtered to only those intersecting the geometry.
# % guisection: Query
# %end

# %option
# % key: datetime
# % label: Datetime Filter
# % description: Either a single datetime or datetime range used to filter results.
# % required: no
# % guisection: Query
# %end

# %option
# % key: query
# % description: List or JSON of query parameters as per the STAC API query extension.
# % required: no
# % guisection: Query
# %end

# %option
# % key: filter
# % description: JSON of query parameters as per the STAC API filter extension
# % required: no
# % guisection: Query
# %end

# %option
# % key: asset_keys
# % label: Asset Keys
# % type: string
# % required: no
# % multiple: yes
# % description: List of one or more asset keys to filter item downloads. \nUse -d (dry run) option to get a list of available asset keys.
# % guisection: Query
# %end

# %option
# % key: filter_lang
# % type: string
# % required: no
# % multiple: no
# % options: cql2-json,cql2-text
# % description: Language variant used in the filter body. If filter is a dictionary or not provided, defaults to ‘cql2-json’. If filter is a string, defaults to cql2-text.
# % guisection: Query
# %end

# %option
# % key: sortby
# % description: A single field or list of fields to sort the response by
# % required: no
# % guisection: Query
# %end

# %option
# % key: format
# % type: string
# % required: no
# % multiple: no
# % options: json,plain
# % description: Output format
# % guisection: Output
# % answer: json
# %end

# %option G_OPT_STRDS_OUTPUT
# % key: strds_output
# % description: (WIP) Data will be imported as a space time dataset.
# % required: no
# % multiple: no
# % guisection: Output
# %end

# %option
# % key: items_vector
# % type: string
# % description: Name of vector containing STAC item boundaries and metadata.
# % required: no
# % multiple: no
# % guisection: Output
# %end

# %option
# % key: method
# % type: string
# % required: no
# % multiple: no
# % options: nearest,bilinear,bicubic,lanczos,bilinear_f,bicubic_f,lanczos_f
# % description: Resampling method to use for reprojection (required if location projection not longlat)
# % descriptions: nearest;nearest neighbor;bilinear;bilinear interpolation;bicubic;bicubic interpolation;lanczos;lanczos filter;bilinear_f;bilinear interpolation with fallback;bicubic_f;bicubic interpolation with fallback;lanczos_f;lanczos filter with fallback
# % guisection: Output
# % answer: nearest
# %end

# %option
# % key: resolution
# % type: string
# % required: no
# % multiple: no
# % options: estimated,value,region
# % description: Resolution of output raster map (default: estimated)
# % descriptions: estimated;estimated resolution;value; user-specified resolution;region;current region resolution
# % guisection: Output
# % answer: estimated
# %end

# %option
# % key: resolution_value
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of output raster map (use with option resolution=value)
# % guisection: Output
# %end

# %option
# % key: extent
# % type: string
# % required: no
# % multiple: no
# % options: input,region
# % description: Output raster map extent
# % descriptions: input;extent of input map;region; extent of current region
# % guisection: Output
# % answer: input
# %end

# %option
# % key: user_name
# % type: string
# % required: no
# % multiple: no
# % description: Basic Auth username
# % guisection: Authentication
# %end

# %option
# % key: userpass
# % label: Password
# % type: string
# % required: no
# % multiple: no
# % description: Basic Auth password
# % guisection: Authentication
# %end

# %option
# % key: token
# % label: API Token
# % type: string
# % required: no
# % multiple: no
# % description: API Token
# % guisection: Authentication
# %end

# %option
# % key: pc_subscription_key
# % label: Planetary Computer Subscription Key
# % type: string
# % required: no
# % multiple: no
# % description: Your Planetary Computer Subscription Key (Ocp-Apim-Subscription-Key)
# % guisection: Authentication
# %end

# %flag
# % key: m
# % description: metadata only
# %end

# %flag
# % key: d
# % description: Dowload and import assets
# %end

# %flag
# % key: p
# % description: Patch data
# %end

# %option G_OPT_M_NPROCS
# %end

# %option G_OPT_MEMORYMB
# %end

import os
import sys
from pprint import pprint
import json

# from multiprocessing.pool import ThreadPool
from pystac_client import Client
from pystac_client.exceptions import APIError
from pystac import MediaType

try:
    from pystac_client import Client
except ImportError:
    from pystac_client import Client


import grass.script as gs
from grass.pygrass.utils import get_lib_path

path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)

import staclib as libstac


def validate_collections_option(client, collections=[]):
    """Validate that the collection the user specificed is valid

    Args:
        collections (String[]): User defined collection
        client (Client): A PyStac Client

    Returns:grass r.import unable to determine number raster bands
        boolean: Returns true if the collection is available.
    """
    try:
        available_collections = client.get_collections()
    except APIError as e:
        gs.fatal(_("Error getting collections: {}".format(e)))

    available_collections_ids = [c.id for c in list(available_collections)]

    # gs.message(_(f"Available Collections: {available_collections_ids}"))

    if all(item in available_collections_ids for item in collections):
        return True

    for collection in collections:
        if collection not in available_collections_ids:
            gs.warning(_(f"{collection} collection not found"))

    return False


def search_stac_api(client, **kwargs):
    """Search the STAC API"""
    try:
        search = client.search(**kwargs)
    except APIError as e:
        gs.fatal(_("Error searching STAC API: {}".format(e)))
    except NotImplementedError as e:
        gs.fatal(_("Error searching STAC API: {}".format(e)))
    except Exception as e:
        gs.fatal(_("Error searching STAC API: {}".format(e)))

    try:
        gs.message(_(f"Search Matched: {search.matched()} items"))
        gs.message(_(f"Pages: {len(list(search.pages()))}"))
        gs.message(_(f"Max items per page: {len(list(search.items()))}"))

    except e:
        gs.warning(_(f"No items found: {e}"))
        return None

    return search


def collection_metadata(collection):
    """Get collection"""

    gs.message(_("*" * 80))
    gs.message(_(f"Collection Id: {collection.id}"))

    libstac.print_attribute(collection, "title", "Collection Title")
    libstac.print_attribute(collection, "description", "Description")
    gs.message(_(f"Spatial Extent: {collection.extent.spatial.bboxes}"))
    gs.message(_(f"Temporal Extent: {collection.extent.temporal.intervals}"))

    libstac.print_attribute(collection, "license")
    libstac.print_attribute(collection, "keywords")
    libstac.print_attribute(collection, "links")
    libstac.print_attribute(collection, "providers")
    libstac.print_attribute(collection, "stac_extensions", "Extensions")

    try:
        gs.message(_("\n# Summaries:"))
        libstac.print_summary(collection.summaries.to_dict())
    except AttributeError:
        gs.info(_("Summaries not found."))

    try:
        gs.message(_("\n# Extra Fields:"))
        libstac.print_summary(collection.extra_fields)
    except AttributeError:
        gs.info(_("# Extra Fields not found."))

    return collection.to_dict()


def report_stac_item(item):
    """Print a report of the STAC item to the console."""
    gs.message(_(f"Collection ID: {item.collection_id}"))
    gs.message(_(f"Item: {item.id}"))
    gs.message(_(f"Geometry: {item.geometry}"))
    gs.message(_(f"Bbox: {item.bbox}"))

    libstac.print_attribute(item, "datetime", "Datetime")
    libstac.print_attribute(item, "start_datetime", "Start Datetime")
    libstac.print_attribute(item, "end_datetime", "End Datetime")

    gs.message(_(f"Links: {item.links}"))

    libstac.print_attribute(item, "extra_fields", "Extra Fields")
    libstac.print_attribute(item, "stac_extensions", "Extensions")

    gs.message(_(f"Properties: {item.properties}"))


def import_items(items, asset_keys=None, roles=None):
    """Import items"""

    # PARQUET = "application/x-parquet"
    # NETCDF = "application/x-netcdf"
    # ZARR = "application/x-zarr"

    VECTOR_MEDIA_TYPES = [
        MediaType.GEOJSON,
        MediaType.GEOPACKAGE,
        MediaType.FLATGEOBUF,
        MediaType.JSON,
        MediaType.TEXT,
        MediaType.XML,
        # PARQUET
    ]

    RASTER_MEDIA_TYPES = [
        MediaType.GEOTIFF,
        MediaType.COG,
        MediaType.JPEG,
        MediaType.PNG,
        MediaType.TIFF,
        MediaType.JPEG2000,
    ]

    HDF_MEDIA_TYPES = [MediaType.HDF5, MediaType.HDF]

    asset_download_list = []
    asset_name_list = []

    for item in items:
        report_stac_item(item)
        # print_summary(item.to_dict())
        for key, asset in item.assets.items():
            media_type = asset.media_type
            if asset_keys and key not in asset_keys:
                continue

            # gs.message(_("\nAsset"))
            # gs.message(_(f"Asset Key: {key}"))
            # gs.message(_(f"Asset Title: {asset.title}"))
            # gs.message(_(f"Asset Description: {asset.description}"))
            # gs.message(_(f"Asset Media Type: {media_type}"))
            # gs.message(_(f"Asset Roles: {asset.roles}"))
            # gs.message(_(f"Asset Href: {asset.href}"))

            # if media_type == MediaType.COG:
            #     url = asset.href
            #     asset_download_list.append(url)
            #     asset_name = os.path.splitext(os.path.basename(url))[0]
            #     asset_name_list.append(f"{item.id}.{asset_name}")

            #     gs.message(_(f"Asset added to download queue: {asset.to_dict()} \n"))

            if media_type in RASTER_MEDIA_TYPES:
                url = asset.href
                asset_download_list.append(url)
                asset_name = os.path.splitext(os.path.basename(url))[0]
                asset_name_list.append(f"{item.id}.{asset_name}")

                gs.message(_(f"Asset added to download queue: {asset.to_dict()} \n"))

            # if media_type in VECTOR_MEDIA_TYPES:
            #     url = asset.href
            #     asset_download_list.append(url)
            #     asset_name = os.path.splitext(os.path.basename(url))[0]
            #     asset_name_list.append(f"{item.id}.{asset_name}")

        gs.message(_("*" * 80))

    return [asset_download_list, asset_name_list]


def main():
    """Main function"""

    # STAC Client options
    client_url = options["url"]  # required
    collection_id = options["collection_id"]  # required

    # Authentication options
    user_name = options["user_name"]  # optional
    userpass = options["userpass"]  # optional
    token = options["token"]  # optional
    pc_subscription_key = options["pc_subscription_key"]  # optional

    # Request options
    limit = int(options["limit"])  # optional
    max_items = int(options["max_items"])  # optional
    request_method = options["request_method"]  # optional

    # Query options
    bbox = options["bbox"]  # optional
    datetime = options["datetime"]  # optional
    query = options["query"]  # optional
    filter = options["filter"]  # optional
    filter_lang = options["filter_lang"]  # optional
    intersects = options["intersects"]  # optional
    # Asset options
    asset_keys_input = options["asset_keys"]  # optional
    asset_keys = asset_keys_input.split(",") if asset_keys_input else None

    # Flags
    metadata_only = flags["m"]
    download = flags["d"]
    patch = flags["p"]

    # Output options
    strds_output = options["strds_output"]  # optional
    items_vector = options["items_vector"]  # optional
    method = options["method"]  # optional
    resolution = options["resolution"]  # optional
    resolution_value = options["resolution_value"]  # optional
    extent = options["extent"]  # optional
    format = options["format"]  # optional

    # GRASS import options
    method = options["method"]  # optional
    memory = int(options["memory"])  # optional
    nprocs = int(options["nprocs"])  # optional

    search_params = {}  # Store STAC API search parameters
    collection_items_output = []
    dowload_items_assests_queue = []

    try:

        req_headers = libstac.set_request_headers(
            username=user_name,
            password=userpass,
            token=token,
            pc_subscription_key=pc_subscription_key,
        )

        client = Client.open(client_url, headers=req_headers)
    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))

    try:
        collection = client.get_collection(collection_id)
    except APIError as e:
        gs.fatal(_(f"Error getting collection {collection_id}: {e}"))

    if metadata_only and format == "plain":
        collection_metadata(collection)
        return 0

    if format == "json" and metadata_only:
        return pprint(collection.to_dict())

    # Start item search
    intersects = options["intersects"]  # optional
    if intersects:
        # Convert the vector to a geojson
        output_geojson = "tmp_stac_intersects.geojson"
        gs.run_command(
            "v.out.ogr", input=intersects, output=output_geojson, format="GeoJSON"
        )
        with open(output_geojson, "r") as f:
            intersects_geojson = f.read()
            search_params["intersects"] = intersects_geojson
            f.close()
        os.remove(output_geojson)

    if options["ids"]:
        ids = options["ids"]  # item ids optional
        search_params["ids"] = ids.split(",")

    # Set the bbox to the current region if the user did not specify the bbox or intersects option
    if not bbox and not intersects:
        gs.message(_("Setting bbox to current region: {}".format(bbox)))
        bbox = libstac.region_to_wgs84_decimal_degrees_bbox()

    if datetime:
        search_params["datetime"] = datetime

    # Add filter to search_params
    # https://github.com/stac-api-extensions/filter
    if filter:
        if isinstance(filter, str):
            filter = json.loads(filter)
        if isinstance(filter, dict):
            search_params["filter"] = filter

    if filter_lang:
        search_params["filter_lang"] = filter_lang

    if query:
        if isinstance(query, str):
            query = json.loads(query)
        if isinstance(query, dict):
            search_params["query"] = query
        if isinstance(query, list):
            search_params["query"] = query

    # Add search parameters to search_params
    search_params["method"] = request_method
    search_params["collections"] = collection_id
    search_params["limit"] = limit
    search_params["max_items"] = max_items
    search_params["bbox"] = bbox

    # Search the STAC API
    items_search = search_stac_api(client=client, **search_params)
    if items_vector:
        libstac.create_vector_from_feature_collection(
            "stac_items", items_search.item_collection_as_dict()
        )
    if metadata_only:
        return pprint(json.dumps(items_search.item_collection_as_dict()))

    # asset_list, asset_name_list = import_items(
    #     list(items_search.items()), asset_keys
    # )
    # gs.message(_(f"{len(asset_list)} Assets Ready for download..."))
    return None


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
