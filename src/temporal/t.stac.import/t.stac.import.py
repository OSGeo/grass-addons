#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.import
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Import data into GRASS from SpatioTemporal Asset Catalogs (STAC) APIs.
# COPYRIGHT:    (C) 2024 Corey White
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
# % description: STAC API Client URL (examples at https://stacspec.org/en/about/datasets/ )
# % required: yes
# %end

# %option
# % key: request_method
# % type: string
# % required: yes
# % multiple: no
# % options: GET,POST
# % answer: POST
# % description:  The HTTP method to use when making a request to the service.
# %end

# %flag
# % key: s
# % description: Is static catalog
# %end

# %flag
# % key: c
# % description: Get the available collections then exit
# %end

# %flag
# % key: i
# % description: Get the available items from collections then exit
# %end

# %flag
# % key: d
# % description: (Dry-run) Get the available assets from collections then before download and then exit
# %end

# %option
# % key: collections
# % type: string
# % required: no
# % multiple: yes
# % description: List of one or more Collection IDs or pystac.Collection instances. Only Items in one of the provided Collections will be searched
# % guisection: Request
#%end

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
# % guisection: Request
# %end

# %option
# % key: bbox
# % type: double
# % required: no
# % multiple: yes
# % description: The bounding box of the request in WGS84 (example [-72.5,40.5,-72,41]). (default is current region)
# % guisection: Request
# %end

# %option G_OPT_V_INPUT
# % key: intersects
# % required: no
# % description: Results filtered to only those intersecting the geometry.
# % guisection: Request
# %end

# %option
# % key: datetime
# % label: Datetime Filter
# % description: Either a single datetime or datetime range used to filter results.
# % required: no
# % guisection: Request
# %end

# %option
# % key: query
# % description: List or JSON of query parameters as per the STAC API query extension.
# % required: no
# % guisection: Request
# %end

# %option
# % key: filter
# % description: JSON of query parameters as per the STAC API filter extension
# % required: no
# % guisection: Request
# %end

# %option
# % key: filter_lang
# % description: Language variant used in the filter body. If filter is a dictionary or not provided, defaults to ‘cql2-json’. If filter is a string, defaults to cql2-text.
# % required: no
# % guisection: Request
# %end

# %option
# % key: filter_lang
# % type: string
# % required: no
# % multiple: no
# % options: cql2-json,cql2-text
# % description: Language variant used in the filter body. If filter is a dictionary or not provided, defaults to ‘cql2-json’. If filter is a string, defaults to cql2-text.
# % guisection: Request
# %end

# %option
# % key: sortby
# % description: A single field or list of fields to sort the response by
# % required: no
# % guisection: Request
# %end

# %option G_OPT_STRDS_OUTPUT
# % key: strds_output
# % description: Data will be imported as a space time dataset.
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
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of output raster map (required if location projection not longlat)
# % guisection: Output
# %end

#%option G_OPT_M_NPROCS
#%end

#%option G_OPT_MEMORYMB
#%end

import os
import sys
import json
import requests

# from multiprocessing.pool import ThreadPool
from pystac_client import Client
from pystac_client.exceptions import APIError
from pystac import MediaType
from pystac import Catalog

import grass.script as gs
from grass.exceptions import CalledModuleError
from urllib3.exceptions import NewConnectionError

try:
    from pystac_client import Client
except ImportError:
    from pystac_client import Client
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm


def region_to_wgs84_decimal_degrees_bbox():
    """convert region bbox to wgs84 decimal degrees bbox"""
    region = gs.parse_command("g.region", quiet=True, flags="ubg")
    bbox = [
        float(c)
        for c in [region["ll_w"], region["ll_s"], region["ll_e"], region["ll_n"]]
    ]
    gs.message(_("BBOX: {}".format(bbox)))
    return bbox


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

    gs.message(_(f"Available Collections: {available_collections_ids}"))

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
    gs.message(_(f"{search.matched()} items found"))
    return search


def check_url_type(url):
    """
    Check if the URL is 's3://', 'gs://', or 'http(s)://'.

    Parameters:
    - url (str): The URL to check.

    Returns:
    - str: 's3', 'gs', 'http', or 'unknown' based on the URL type.
    """
    if url.startswith("s3://"):
        return url.replace("s3://", "/vsis3/")
    elif url.startswith("gs://"):
        return url.replace("gs://", "/vsigs/")
    elif url.startswith("http://") or url.startswith("https://"):
        return url
    else:
        gs.message(_(f"Unknown Protocol: {url}"))
        return "unknown"


def import_grass_raster(params):
    url, output, resample_method, memory = params

    input_url = check_url_type(url)

    try:
        gs.message(_(f"Importing: {output}"))
        gs.parse_command(
            "r.import",
            input=input_url,
            output=output,
            resample=resample_method,
            memory=memory,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error importing raster: {}".format(e.stderr)))


def create_strds(strds_output, asset_name_list):
    """Create a space-time raster dataset and add the imported rasters to it."""
    gs.parse_command("t.create", output=strds_output, type="strds", title=strds_output)
    for asset_name in asset_name_list:
        gs.parse_command(
            "t.register", input=asset_name, type="rast", output=strds_output
        )


def download_assets(urls, filenames, resample_method, memory, nprocs=1):
    """Downloads a list of images from the given URLs to the given filenames."""
    max_cpus = os.cpu_count() - 1
    if nprocs > max_cpus:
        gs.warning(
            _(
                "Number of processes {nprocs} is greater than the number of CPUs {max_cpus}."
            )
        )
        nprocs = max_cpus

    with tqdm(total=len(urls), desc="Downloading assets") as pbar:
        with ThreadPoolExecutor(max_workers=nprocs) as executor:
            try:
                for _a in executor.map(
                    import_grass_raster, zip(urls, filenames, resample_method, memory)
                ):
                    pbar.update(1)
            except Exception as e:
                gs.fatal(_("Error importing raster: {}".format(str(e))))


def get_all_collections(client):
    """Get a list of collections from STAC Client"""
    try:
        collections = client.get_collections()
        collection_list = list(collections)
        gs.message(_(f"Collections found: {len(collection_list)}"))
        for i in collection_list:
            gs.message(_(i.id))
        return collection_list
    except APIError as e:
        gs.fatal(_("Error getting collections: {}".format(e)))


def generate_indentation(depth):
    """Generate indentation for summary"""
    return "    " * depth


def print_summary(data, depth=1):
    """Print summary of json data recursively increasing indentation."""
    for key, value in data.items():
        indentation = generate_indentation(depth)
        if isinstance(value, dict):
            gs.message(_(f"#\n# {indentation}{key}:"))
            print_summary(value, depth=depth + 1)
        else:
            gs.message(_(f"# {indentation}{key}: {value}"))


def get_collection_items(client, collection_name):
    """Get collection"""
    try:
        collection = client.get_collection(collection_name)
    except APIError as e:
        gs.fatal(_(f"Error getting collection {collection_name}: {e}"))

    gs.message(_("*" * 80))
    gs.message(_(f"Collection Id: {collection.id}"))

    try:
        gs.message(_(f"Collection Title: {collection.title}"))
    except AttributeError:
        gs.info(_("Collection Title not found."))

    gs.message(_(f"Collection Title: {collection.title}"))
    gs.message(_(f"Description: {collection.description}"))
    gs.message(_(f"Spatial Extent: {collection.extent.spatial.bboxes}"))
    gs.message(_(f"Temporal Extent: {collection.extent.temporal.intervals}"))

    try:
        gs.message(_(f"License: {collection.license}"))
    except AttributeError:
        gs.info(_("License information not found."))

    try:
        gs.message(_(f"keywords: {collection.keywords}"))
    except AttributeError:
        gs.info(_("Keywords not found."))

    gs.message(_(f"Links: {collection.links}"))

    try:
        gs.message(_(f"Extensions: {collection.stac_extensions}"))
    except AttributeError:
        gs.info(_("Extensions not found."))

    try:
        gs.message(_("\n# Summaries:"))
        print_summary(collection.summaries.to_dict())
    except AttributeError:
        gs.info(_("Summaries not found."))

    try:
        gs.message(_("\n# Extra Fields:"))
        print_summary(collection.extra_fields)
    except AttributeError:
        gs.info(_("# Extra Fields not found."))

    return collection.to_dict()


# TODO: Complete functionality to import all media types
def import_items(
    items,
    region_params=None,
    reprojection=None,
    output=None,
    method=None,
    resolution=None,
    memory=None,
):
    """Import items"""

    asset_download_list = []
    asset_name_list = []

    for item in items:
        gs.message(_(f"Collection ID: {item.collection_id} \n"))
        gs.message(_(f"Item: {item.id}"))
        gs.message(_(f"Geometry: {item.geometry} \n"))
        gs.message(_(f"Bbox: {item.bbox} \n"))

        try:
            gs.message(_(f"Datetime: {item.datetime} \n"))
        except AttributeError:
            try:
                gs.message(_(f"Start Datetime: {item.start_datetime} \n"))
            except AttributeError:
                gs.info(_("Start Datetime not found."))
            try:
                gs.message(_(f"End Datetime: {item.end_datetime} \n"))
            except AttributeError:
                gs.info(_("End Datetime not found."))

        gs.message(_(f"Links: {item.links} \n"))

        try:
            gs.message(_(f"Extra Fields: {item.extra_fields} \n"))
        except AttributeError:
            gs.info(_("Extra Fields not found."))

        try:
            gs.message(_(f"Extensions: {item.stac_extensions}"))
        except AttributeError:
            gs.info(_("Extensions not found."))

        gs.message(_(f"Properties: {item.properties} \n"))
        # print_summary(item.to_dict())
        for key, asset in item.assets.items():
            media_type = asset.media_type
            # gs.message(_(f"Asset {key}: {media_type} \n"))
            # gs.message(_(f"Asset: {asset.to_dict()} \n"))
            if media_type == MediaType.COG:
                url = asset.href
                asset_download_list.append(url)
                asset_name = os.path.splitext(os.path.basename(url))[0]
                asset_name_list.append(f"{item.id}.{asset_name}")

                gs.message(_(f"Asset added to download queue: {asset.to_dict()} \n"))
            # if media_type == MediaType.GEOTIFF:
            # asset_download_list.append(asset.href)
            # gs.message(_(f"Added asset to download queue: {asset} \n"))
            # if media_type == MediaType.JPEG:
            #     asset_download_list.append(asset.href)
            #     gs.message(_(f"Added asset to download queue: {asset} \n"))
            # if media_type == MediaType.PNG:
            #     asset_download_list.append(asset.href)
            #     gs.message(_(f"Added asset to download queue: {asset} \n"))
            # if media_type == MediaType.TIFF:
            #     asset_download_list.append(asset.href)
            #     gs.message(_(f"Added asset to download queue: {asset} \n"))

            # gs.message(_(f"Asset: {item.assets[asset]} \n"))

        gs.message(_("*" * 80))

    # gs.message(_(f"Asset Download List: {asset_download_list} \n"))
    resample_method_list = [method] * len(asset_download_list)
    memory_list = [memory] * len(asset_download_list)

    return [asset_download_list, asset_name_list, resample_method_list, memory_list]


def main():
    """Main function"""

    search_params = {}  # Store STAC API search parameters

    # STAC Client options
    client_url = options["url"]  # required
    request_method = options["request_method"]  # required
    collection_input = options["collections"]  # Maybe limit to one?
    collections = collection_input.split(",")
    limit = int(options["limit"])  # optional
    max_items = int(options["max_items"])  # optional
    bbox = options["bbox"]  # optional
    datetime = options["datetime"]  # optional
    query = options["query"]  # optional
    filter = options["filter"]  # optional
    filter_lang = options["filter_lang"]  # optional

    intersects = options["intersects"]  # optional
    if intersects:
        # Convert the vector to a geojson
        # I don't love this is their a better way to do this?
        output_geojson = "tmp_stac_intersects.geojson"
        gs.run_command(
            "v.out.ogr", input=intersects, output=output_geojson, format="GeoJSON"
        )
        with open(output_geojson, "r") as f:
            intersects_geojson = f.read()
            search_params["intersects"] = intersects_geojson
            f.close()
        os.remove(output_geojson)

    # GRASS import options
    method = options["method"]  # optional
    memory = int(options["memory"])  # optional
    nprocs = int(options["nprocs"])
    # resolution = options["resolution"]  # optional

    # Output options
    strds_output = options["strds_output"]  # optional
    # output = options["output"]  # optional

    try:
        client = Client.open(client_url)
        gs.message(_(f"Client Id: {client.id}"))
        gs.message(_(f"Client Title: {client.title}"))
        gs.message(_(f"Client Title: {client.description}"))
        gs.message(_(f"Client STAC Extensions: {client.stac_extensions}"))
        gs.message(_(f"Client Extra Fields: {client.extra_fields}"))
        gs.message(_(f"Client links: {client.links}"))
        gs.message(_(f"Client catalog_type: {client.catalog_type}"))
    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))

    # Is static catalog not STAC API
    # TODO: Finish figuring out how to handle static catalogs
    is_static_catalog = flags["s"]
    if is_static_catalog:
        gs.message(_(f"Fetching Static Catalog: {client_url}"))
        try:
            client = Catalog.from_file(client_url)
            gs.message(_(f"Catalog: {client.to_dict()}"))
            collections = client.get_collections()
            collection_list = list(collections)
            gs.message(_(f"Collections: {collection_list}"))

            for collection in collection_list:
                gs.message(_(f"Collection: {collection}"))
                collection_items = collection.get_items()
                item_list = list(collection_items)
                gs.message(_(f"Items: {item_list}"))
        except requests.exceptions.RequestException as e:
            gs.fatal(_("Error making request to STAC API: {}".format(e)))
        except ValueError as e:
            gs.fatal(_("Error decoding STAC catalog: {}".format(e)))

    # Parse flags
    collections_only = flags["c"]
    collection_itmes_only = flags["i"]
    dry_run = flags["d"]

    if collections_only:
        get_all_collections(client)
        return None

    if collection_itmes_only:
        for collection in collections:
            get_collection_items(client, collection)
        return None

    if options["ids"]:
        ids = options["ids"]  # item ids optional
        search_params["ids"] = ids.split(",")

    # Set the bbox to the current region if the user did not specify the bbox or intersects option
    if not bbox and not intersects:
        gs.message(_("Setting bbox to current region: {}".format(bbox)))
        bbox = region_to_wgs84_decimal_degrees_bbox()

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
    search_params["collections"] = collections
    search_params["limit"] = limit
    search_params["max_items"] = max_items
    search_params["bbox"] = bbox

    if validate_collections_option(client, collections):
        items_search = search_stac_api(client=client, **search_params)
        gs.message(_("Import Items..."))
        asset_list, asset_name_list, method_list, memory_list = import_items(
            list(items_search.items()), method=method, memory=memory
        )
        gs.message(_(f"{len(asset_list)} Assets Ready for download..."))

        if not dry_run:
            download_assets(
                asset_list, asset_name_list, method_list, memory_list, nprocs
            )
            if strds_output:
                create_strds(strds_output, asset_name_list)
                # TODO: Register the space time raster dataset
    else:
        gs.warning(_(f"Invalid Collections: {collections}"))


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
