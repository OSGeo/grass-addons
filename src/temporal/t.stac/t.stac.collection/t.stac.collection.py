#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.collection
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      View SpatioTemporal Asset Catalogs (STAC) collection.
# COPYRIGHT:    (C) 2023-2024 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

# %module
# % description: Get STAC API collection metadata
# % keyword: temporal
# % keyword: STAC
# % keyword: collection
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
# % key: collection_id
# % description: Collection ID
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


from pystac_client import Client
from pystac_client.exceptions import APIError
from pystac_client.conformance import ConformanceClasses

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
    collection_id = options["collection_id"]  # optional
    # vector_metadata = options["vector_metadata"]  # optional

    # Output format
    format = options["format"]  # optional

    # Flag options
    basic_info = flags["b"]  # optional

    # Set the request headers
    settings = options["settings"]
    req_headers = libstac.set_request_headers(settings)

    try:
        client = Client.open(client_url, headers=req_headers)
    except APIError as e:
        gs.fatal(_("APIError Error opening STAC API: {}".format(e)))

    if libstac.conform_to_collections(client):
        gs.verbose(_("Conforms to STAC Collections"))

    if collection_id:
        try:
            collection = client.get_collection(collection_id)
            collection_dict = collection.to_dict()
            if format == "json":
                gs.message(_(f"collection: {collection}"))
                return collection_dict
                # return pprint(collection.to_dict())
            elif format == "plain":
                if basic_info:
                    return libstac.print_basic_collection_info(collection_dict)
                return libstac.print_summary(collection_dict)

        except APIError as e:
            gs.fatal(_("APIError Error getting collection: {}".format(e)))

    # Create metadata vector
    # if vector_metadata:
    #     gs.message(_(f"Outputting metadata to {vector_metadata}"))
    #     libstac.create_metadata_vector(vector_metadata, collection_list)
    #     gs.message(_(f"Metadata written to {vector_metadata}"))
    #     return vector_metadata


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
