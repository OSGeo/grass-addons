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
# % description: The HTTP method to use when making a request to the service.
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

# %flag
# % key: p
# % description: Pretty print the JSON output
# %end

import sys
import json
from io import StringIO
from contextlib import contextmanager
from pprint import pprint
import grass.script as gs
from grass.pygrass.utils import get_lib_path


@contextmanager
def add_sys_path(new_path):
    """Add a path to sys.path and remove it when done"""
    original_sys_path = sys.path[:]
    sys.path.append(new_path)
    try:
        yield
    finally:
        sys.path = original_sys_path


path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)


def main():
    """Main function"""

    # Import dependencies
    path = get_lib_path(modname="t.stac", libname="staclib")
    if path is None:
        gs.fatal("Not able to find the stac library directory.")

    with add_sys_path(path):
        try:
            import staclib as libstac
        except ImportError as err:
            gs.fatal(f"Unable to import staclib: {err}")

    # STAC Client options
    client_url = options["url"]  # required
    format = options["format"]  # optional

    # Flag options
    basic_info = flags["b"]  # optional
    pretty_print = flags["p"]  # optional

    # Set the request headers
    settings = options["settings"]
    req_headers = libstac.set_request_headers(settings)

    try:
        stac_helper = libstac.STACHelper()
        client = stac_helper.connect_to_stac(client_url, req_headers)

        # Check if the client conforms to the STAC Item Search
        # This will exit the program if the client does not conform
        stac_helper.conforms_to_item_search()

        if format == "plain":
            sys.stdout.write(f"{'-' * 75}\n")
            sys.stdout.write(f"Catalog: {client.title}\n")
            sys.stdout.write(f"{'-' * 75}\n")
            sys.stdout.write(f"Client Id: {client.id}\n")
            sys.stdout.write(f"Client Description: {client.description}\n")
            sys.stdout.write(f"Client STAC Extensions: {client.stac_extensions}\n")
            sys.stdout.write(f"Client catalog_type: {client.catalog_type}\n")
            sys.stdout.write(f"{'-' * 75}\n")

            # Get all collections
            collection_list = stac_helper.get_all_collections()
            sys.stdout.write(f"Collections: {len(collection_list)}\n")
            sys.stdout.write(f"{'-' * 75}\n")

            if basic_info:
                for i in collection_list:
                    sys.stdout.write(f"{i.get('id')}: {i.get('title')}\n")
            else:
                for i in collection_list:
                    sys.stdout.write(f"Collection: {i.get('title')}\n")
                    sys.stdout.write(f"{'-' * 75}\n")
                    sys.stdout.write(f"Collection Id: {i.get('id')}\n")
                    sys.stdout.write(f"{i.get('description')}\n")
                    sys.stdout.write(f"Extent: {i.get('extent')}\n")
                    sys.stdout.write(f"License: {i.get('license')}\n")
                    sys.stdout.write(f"{'-' * 75}\n")
                    libstac.print_list_attribute(
                        client.get_conforms_to(), "Conforms To:"
                    )
                    sys.stdout.write(f"{'-' * 75}\n")
                return None
        else:
            client_dict = client.to_dict()
            if pretty_print:
                output = StringIO()
                pprint(client_dict, stream=output)
                sys.stdout.write(output.getvalue())
            else:
                json_output = json.dumps(client.to_dict())
                sys.stdout.write(json_output)

    except Exception as e:
        gs.fatal(_("Error: {}".format(e)))


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
