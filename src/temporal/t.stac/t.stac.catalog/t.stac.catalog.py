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
# % keyword: temporal
# % keyword: STAC
# % keyword: catalog
# % keyword: metadata
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
# % key: format
# % type: string
# % required: no
# % multiple: no
# % options: json,plain
# % description: Output format
# % guisection: Output
# % answer: json
# %end

# %flag
# % key: b
# % description: Return basic information only
# %end

import sys
from pprint import pprint
import grass.script as gs
from grass.pygrass.utils import get_lib_path

# Import STAC Client
from pystac_client import Client
from pystac_client.exceptions import APIError
import json


path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)


def main():
    """Main function"""
    import staclib as libstac

    # STAC Client options
    client_url = options["url"]  # required
    format = options["format"]  # optional

    # Flag options
    basic_info = flags["b"]  # optional

    # Set the request headers
    settings = options["settings"]
    req_headers = libstac.set_request_headers(settings)

    try:
        client = Client.open(client_url, headers=req_headers)

        # Check if the client conforms to the STAC Item Search
        # This will exit the program if the client does not conform
        libstac.conform_to_item_search(client)

        if format == "plain":
            gs.message(_(f"Client Id: {client.id}"))
            gs.message(_(f"Client Title: {client.title}"))
            gs.message(_(f"Client Description: {client.description}"))
            gs.message(_(f"Client STAC Extensions: {client.stac_extensions}"))
            gs.message(_(f"Client Extra Fields: {client.extra_fields}"))
            gs.message(_(f"Client catalog_type: {client.catalog_type}"))
            gs.message(_(f"{'-' * 75}\n"))

            # Get all collections
            collection_list = libstac.get_all_collections(client)
            gs.message(_(f"Collections: {len(collection_list)}\n"))
            gs.message(_(f"{'-' * 75}\n"))

            if basic_info:
                for i in collection_list:
                    gs.message(_(f"{i.get('id')}: {i.get('title')}"))

            if not basic_info:
                for i in collection_list:
                    gs.message(_(f"{i.get('id')}: {i.get('title')}"))
                    gs.message(_(f"{i.get('description')}"))
                    gs.message(_(f"Extent: {i.get('extent')}"))
                    gs.message(_(f"License: {i.get('license')}"))
                    gs.message(_(f"{'-' * 75}\n"))
                    libstac.print_list_attribute(
                        client.get_conforms_to(), "Conforms To:"
                    )
                    gs.message(_(f"{'-' * 75}\n"))
                return None
        else:
            json_output = json.dumps(client.to_dict())
            return json_output

    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
