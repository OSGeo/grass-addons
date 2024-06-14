#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.catalog
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      View SpatioTemporal Asset Catalogs (STAC) collection.
# COPYRIGHT:    (C) 2024 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Get STAC API Catalog metadata
# % keyword: raster
# % keyword: catalog
# % keyword: STAC
# % keyword: temporal
# %end

# %option
# % key: url
# % description: STAC API Client URL (examples at https://stacspec.org/en/about/datasets/)
# % type: string
# % required: yes
# % multiple: no
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
# % key: b
# % description: basic info
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

import sys
from pprint import pprint
import grass.script as gs
from grass.pygrass.utils import get_lib_path

try:
    from pystac_client import Client
    from pystac_client.exceptions import APIError
except ImportError:
    from pystac_client import Client

path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)


def get_all_collections(client):
    """Get a list of collections from STAC Client"""
    try:
        collections = client.get_collections()
        collection_list = list(collections)
        return [i.to_dict() for i in collection_list]

    except APIError as e:
        gs.fatal(_("Error getting collections: {}".format(e)))


def main():
    """Main function"""
    import staclib as libstac

    # STAC Client options
    client_url = options["url"]  # required

    # Flag options
    basic_info = flags["b"]  # optional

    # Authentication options
    user_name = options["user_name"]  # optional
    userpass = options["userpass"]  # optional
    token = options["token"]  # optional

    # Set the request headers
    req_headers = libstac.set_request_headers(
        username=user_name, password=userpass, token=token
    )

    try:
        client = Client.open(client_url, headers=req_headers)

        if basic_info:
            gs.message(_(f"Client Id: {client.id}"))
            gs.message(_(f"Client Title: {client.title}"))
            gs.message(_(f"Client Description: {client.description}"))
            gs.message(_(f"Client STAC Extensions: {client.stac_extensions}"))
            gs.message(_(f"Client Extra Fields: {client.extra_fields}"))
            gs.message(_(f"Client catalog_type: {client.catalog_type}"))

            # Get all collections
            collection_list = get_all_collections(client)
            if basic_info:
                gs.message(_(f"Collections: {len(collection_list)}\n"))
                for i in collection_list:
                    gs.message(_(f"{i.get('id')}: {i.get('title')}"))
                return None
        else:
            pprint(client.to_dict())

    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
