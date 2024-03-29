#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.item
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Get items from a STAC API server
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
# % key: collections
# % type: string
# % required: yes
# % multiple: yes
# % description: List of one or more Collection IDs or pystac. Collection instances.
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


import os
import sys
import pprint

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

    gs.message(_(f"Available Collections: {available_collections_ids}"))

    if all(item in available_collections_ids for item in collections):
        return True

    for collection in collections:
        if collection not in available_collections_ids:
            gs.warning(_(f"{collection} collection not found"))

    return False


def get_collection_items(client, collection_name):
    """Get collection"""
    try:
        collection = client.get_collection(collection_name)
    except APIError as e:
        gs.fatal(_(f"Error getting collection {collection_name}: {e}"))

    gs.message(_("*" * 80))
    gs.message(_(f"Collection Id: {collection.id}"))

    libstac.print_attribute(collection, "title", "Collection Title")

    gs.message(_(f"Description: {collection.description}"))
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


# TODO: Complete functionality to import all media types
def import_items(items, asset_keys=None):
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

            gs.message(_("\nAsset"))
            gs.message(_(f"Asset Key: {key}"))
            gs.message(_(f"Asset Title: {asset.title}"))
            gs.message(_(f"Asset Description: {asset.description}"))
            gs.message(_(f"Asset Media Type: {media_type}"))
            gs.message(_(f"Asset Roles: {asset.roles}"))
            gs.message(_(f"Asset Href: {asset.href}"))

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
    collection_input = options["collections"]  # Maybe limit to one?
    collections = collection_input.split(",")

    # Authentication options
    user_name = options["user_name"]  # optional
    userpass = options["userpass"]  # optional
    token = options["token"]  # optional
    pc_subscription_key = options["pc_subscription_key"]  # optional

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

    collection_items = get_collection_items(client, collections)
    pprint(collection_items)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
