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

# %flag
# % key: c
# % description: Get the available collections then exit
# % guisection: Request
# %end

# %flag
# % key: i
# % description: Get the available items from collections then exit
# % guisection: Request
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
# % key: sortby
# % description: A single field or list of fields to sort the response by
# % required: no
# % guisection: Request
# %end

# %option G_OPT_R_OUTPUT
# % key: output
# % description: The output raster
# % required: no
# % multiple: no
# % guisection: Output
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

# from multiprocessing.pool import ThreadPool
from pystac_client import Client
from pystac import MediaType
import grass.script as gs
from grass.exceptions import CalledModuleError

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
    available_collections = client.get_collections()
    available_collections_ids = [c.id for c in list(available_collections)]

    gs.warning(_(f"Available Collections: {available_collections_ids}"))

    if collections in available_collections_ids:
        return True

    for collection in collections:
        if collection not in available_collections_ids:
            gs.warning(_(f"{collection} collection not found"))

    return False


def search_stac_api(client, **kwargs):
    """Search the STAC API"""
    search = client.search(**kwargs)
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
    collections = client.get_collections()
    collection_list = list(collections)
    gs.message(_(f"{len(collection_list)} collections found:"))
    for i in collection_list:
        gs.message(_(i.id))
    return collection_list


def print_summary(data):
    """Print summary of json data"""
    for key, value in data.items():
        if isinstance(value, dict):
            gs.message(_(f"{key}:"))
            for subkey, subvalue in value.items():
                gs.message(_(f"  {subkey}: {subvalue}"))
        else:
            gs.message(_(f"{key}: {value}"))


def get_collection_items(client, collection_name):
    """Get collection"""
    collection = client.get_collection(collection_name)
    gs.message(_(f"Collection: {collection.title}"))
    gs.message(_(f"Description: {collection.description}"))
    gs.message(_(f"Spatial Extent: {collection.extent.spatial.bboxes}"))
    gs.message(_(f"Temporal Extent: {collection.extent.temporal.intervals}"))
    gs.message(_(f"License: {collection.license}"))
    gs.message(_(f"Links: {collection.links}"))
    gs.message(_("Properties..."))
    print_summary(collection.extra_fields)
    return collection


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
        gs.message(_(f"Item: {item.id}"))
        gs.message(_(f"Spatial Extent: {item.geometry} \n"))
        gs.message(_(f"Temporal Extent: {item.datetime} \n"))
        gs.message(_(f"Assets: {item.assets} \n"))

        for key, asset in item.assets.items():
            media_type = asset.media_type
            # gs.message(_(f"Asset {key}: {media_type} \n"))
            # gs.message(_(f"Asset: {asset.to_dict()} \n"))
            if media_type == MediaType.COG:
                url = asset.href
                asset_download_list.append(url)
                asset_name = os.path.splitext(os.path.basename(url))[0]
                asset_name_list.append(f"{item.id}.{asset_name}")

                gs.message(_(f"Added asset to download queue: {asset.to_dict()} \n"))
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

        gs.message(_(f"Links: {item.links} \n"))
        gs.message(_(f"Properties: {item.properties} \n"))
        gs.message(_(f"Collection ID: {item.collection_id} \n"))
        gs.message(_("*" * 80))

    gs.message(_(f"Asset Download List: {asset_download_list} \n"))
    resample_method_list = [method] * len(asset_download_list)
    memory_list = [memory] * len(asset_download_list)
    gs.message(_(f"Asset Name List: {asset_name_list} \n"))
    gs.message(_(f"Asset Resample List: {resample_method_list} \n"))
    gs.message(_(f"Asset Memory List: {memory_list} \n"))

    return [asset_download_list, asset_name_list, resample_method_list, memory_list]


def main():
    """Main function"""
    search_params = {}  # Store STAC API search parameters
    client_url = options["url"]
    ids = options["ids"]  # item ids optional
    collections = options["collections"]  # Maybe limit to one?
    limit = int(options["limit"])  # optional
    max_items = int(options["max_items"])  # optional
    bbox = options["bbox"]  # optional

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

    datetime = options["datetime"]  # optional
    if datetime:
        search_params["datetime"] = datetime

    query = options["query"]  # optional
    filter = options["filter"]  # optional
    filter_lang = options["filter_lang"]  # optional

    # GRASS import options
    method = options["method"]  # optional
    memory = int(options["memory"])  # optional
    nprocs = int(options["nprocs"])
    resolution = options["resolution"]  # optional

    # Output options
    strds_output = options["strds_output"]  # optional
    output = options["output"]  # optional

    client = Client.open(client_url)
    gs.message(_(f"Catalog: {client.title}"))

    collections_only = flags["c"]
    collection_itmes_only = flags["i"]

    if collections_only:
        get_all_collections(client)
        return None

    if collection_itmes_only:
        get_collection_items(client, collections)
        return None

    # Set the bbox to the current region if the user did not specify the bbox or intersects option
    if not bbox and not intersects:
        gs.message(_("Setting bbox to current region: {}".format(bbox)))
        bbox = region_to_wgs84_decimal_degrees_bbox()

    # Add search parameters to search_params
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
        download_assets(asset_list, asset_name_list, method_list, memory_list, nprocs)
        if strds_output:
            create_strds(strds_output, asset_name_list)
            # Register the space time raster dataset


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
