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
from pprint import pprint

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

    # gs.message(_(f"Description: {collection.description}"))
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

    collection_items_output = []

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

    for collection in collections:
        if validate_collections_option(client, collections):
            collection_items = get_collection_items(client, collection)
            collection_items_output.append(collection_items)

    return pprint(collection_items_output)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
