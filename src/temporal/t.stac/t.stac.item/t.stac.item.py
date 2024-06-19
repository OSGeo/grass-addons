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

# %option G_OPT_F_INPUT
# % key: settings
# % label: Full path to settings file (user, password)
# % description: '-' for standard input
# % guisection: Request
# % required: no
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
# % description: List of one or more asset keys to filter item downloads.
# % guisection: Query
# %end

# %option
# % key: item_roles
# % label: Item roles
# % type: string
# % required: no
# % multiple: yes
# % description: List of one or more item roles to filter by.
# % guisection: Query
# %end

# %option
# % key: filter_lang
# % type: string
# % required: no
# % multiple: no
# % options: cql2-json,cql2-text
# % description: Language variant used in the filter body. If filter is a dictionary or not provided, defaults to cql2-json. If filter is a string, defaults to cql2-text.
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

# %flag
# % key: m
# % description: Collection Search Item Summary
# %end

# %flag
# % key: i
# % description: Item metadata
# %end

# %flag
# % key: a
# % description: Asset metadata
# %end

# %flag
# % key: d
# % description: Dowload and import assets
# %end

# %flag
# % key: p
# % description: (WIP) Patch data
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
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm

import grass.script as gs
from grass.pygrass.utils import get_lib_path
from grass.exceptions import CalledModuleError


path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)

import staclib as libstac


def search_stac_api(client, **kwargs):
    """Search the STAC API"""
    if libstac.conform_to_item_search(client):
        gs.verbose(_("STAC API Conforms to Item Search"))
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
        # These requests tend to be very slow
        # gs.message(_(f"Pages: {len(list(search.pages()))}"))
        # gs.message(_(f"Max items per page: {len(list(search.items()))}"))

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
    gs.message(_("*" * 80))


def report_stac_item(item):
    """Print a report of the STAC item to the console."""
    gs.message(_(f"Collection ID: {item.collection_id}"))
    gs.message(_(f"Item: {item.id}"))
    libstac.print_attribute(item, "geometry", "Geometry")
    gs.message(_(f"Bbox: {item.bbox}"))

    libstac.print_attribute(item, "datetime", "Datetime")
    libstac.print_attribute(item, "start_datetime", "Start Datetime")
    libstac.print_attribute(item, "end_datetime", "End Datetime")
    gs.message(_("Extra Fields:"))
    libstac.print_summary(item.extra_fields)

    libstac.print_list_attribute(item.stac_extensions, "Extensions:")
    # libstac.print_attribute(item, "stac_extensions", "Extensions")
    gs.message(_("Properties:"))
    libstac.print_summary(item.properties)


def collect_item_assets(item, assset_keys, asset_roles):

    for key, asset in item.assets.items():
        asset_file_name = f"{item.collection_id}.{item.id}.{key}"
        # Check if the asset key is in the list of asset keys
        if assset_keys and key not in assset_keys:
            continue

        # Check if the asset fits the roles
        if asset_roles:
            if not any(role in asset.roles for role in asset_roles):
                continue

        asset_dict = asset.to_dict()
        # The output file name
        asset_dict["collection_id"] = item.collection_id
        asset_dict["item_id"] = item.id
        asset_dict["file_name"] = asset_file_name

        return asset_dict


def report_plain_asset_summary(asset):
    gs.message(_("\nAsset"))
    gs.message(_(f"Asset Item Id: {asset.get('item_id')}"))

    gs.message(_(f"Asset Title: {asset.get('title')}"))
    gs.message(_(f"Asset Filename: {asset.get('file_name')}"))
    gs.message(_(f"Raster bands: {asset.get('raster:bands')}"))
    gs.message(_(f"Raster bands: {asset.get('eo:bands')}"))
    gs.message(_(f"Asset Description: {asset.get('description')}"))
    gs.message(_(f"Asset Media Type: { MediaType(asset.get('type')).name}"))
    gs.message(_(f"Asset Roles: {asset.get('roles')}"))
    gs.message(_(f"Asset Href: {asset.get('href')}"))


def import_grass_raster(params):
    assets, resample_method, extent, resolution, resolution_value, memory = params
    gs.message(_(f"Downloading Asset: {assets}"))
    input_url = libstac.check_url_type(assets["href"])
    gs.message(_(f"Import Url: {input_url}"))

    try:
        gs.message(_(f"Importing: {assets['file_name']}"))
        gs.parse_command(
            "r.import",
            input=input_url,
            output=assets["file_name"],
            resample=resample_method,
            extent=extent,
            resolution=resolution,
            resolution_value=resolution_value,
            title=assets["file_name"],
            memory=memory,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error importing raster: {}".format(e.stderr)))


def download_assets(
    assets,
    resample_method,
    resample_extent,
    resolution,
    resolution_value,
    memory=300,
    nprocs=1,
):
    """Downloads a list of images from the given URLs to the given filenames."""
    number_of_assets = len(assets)
    resample_extent_list = [resample_extent] * number_of_assets
    resolution_list = [resolution] * number_of_assets
    resolution_value_list = [resolution_value] * number_of_assets
    resample_method_list = [resample_method] * number_of_assets
    memory_list = [memory] * number_of_assets
    max_cpus = os.cpu_count() - 1
    if nprocs > max_cpus:
        gs.warning(
            _(
                "Number of processes {nprocs} is greater than the number of CPUs {max_cpus}."
            )
        )
        nprocs = max_cpus

    with tqdm(total=number_of_assets, desc="Downloading assets") as pbar:
        with ThreadPoolExecutor(max_workers=nprocs) as executor:
            try:
                for _a in executor.map(
                    import_grass_raster,
                    zip(
                        assets,
                        resample_method_list,
                        resample_extent_list,
                        resolution_list,
                        resolution_value_list,
                        memory_list,
                    ),
                ):
                    pbar.update(1)
            except Exception as e:
                gs.fatal(_("Error importing raster: {}".format(str(e))))


def main():
    """Main function"""

    # STAC Client options
    client_url = options["url"]  # required
    collection_id = options["collection_id"]  # required

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

    item_roles_input = options["item_roles"]  # optional
    item_roles = item_roles_input.split(",") if item_roles_input else None

    # Flags
    summary_metadata = flags["m"]
    item_metadata = flags["i"]
    asset_metadata = flags["a"]
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
    collection_items_assets = []

    try:

        # Set the request headers
        settings = options["settings"]
        req_headers = libstac.set_request_headers(settings)

        client = Client.open(client_url, headers=req_headers)
    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))

    try:
        collection = client.get_collection(collection_id)
    except APIError as e:
        gs.fatal(_(f"Error getting collection {collection_id}: {e}"))

    if summary_metadata:
        if format == "plain":
            return collection_metadata(collection)
        elif format == "json":
            return pprint(collection.to_dict())
        else:
            # Return plain text by default
            return collection_metadata(collection)

    # Start item search

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

    if libstac.conform_to_query(client):
        gs.verbose(_("STAC API Conforms to Item Search Query"))
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
    # Create vector layer of items metadata
    if items_vector:
        libstac.create_vector_from_feature_collection(
            items_vector, items_search, limit, max_items
        )

    # Fetch items from all pages
    items = libstac.fetch_items_with_pagination(items_search, limit, max_items)

    # Report item metadata
    if item_metadata:
        if format == "plain":
            gs.message(_(f"Items Found: {len(list(items))}"))
            for item in items:
                report_stac_item(item)
            return None
        if format == "json":
            return pprint([item.to_dict() for item in items])

    for item in items:
        asset = collect_item_assets(item, asset_keys, asset_roles=item_roles)
        if asset:
            collection_items_assets.append(asset)

    gs.message(_(f"{len(collection_items_assets)} Assets Ready for download..."))
    if asset_metadata:
        for asset in collection_items_assets:
            if format == "plain":
                report_plain_asset_summary(asset)
            if format == "json":
                pprint(asset)

    if download:
        # Download and Import assets
        download_assets(
            assets=collection_items_assets,
            resample_method=method,
            resample_extent=extent,
            resolution=resolution,
            resolution_value=resolution_value,
            memory=memory,
            nprocs=nprocs,
        )


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
