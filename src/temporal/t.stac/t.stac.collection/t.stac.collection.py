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

# %flag
# % key: p
# % description: Pretty print the JSON output
# %end

import sys
import json
from io import StringIO
from pprint import pprint
from contextlib import contextmanager
import grass.script as gs
from grass.pygrass.utils import get_lib_path

# Add the stac library to the sys.path
path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)


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
    collection_id = options["collection_id"]  # optional
    # vector_metadata = options["vector_metadata"]  # optional

    # Output format
    format = options["format"]  # optional

    # Flag options
    basic_info = flags["b"]  # optional
    pretty_print = flags["p"]  # optional

    # Set the request headers
    settings = options["settings"]
    req_headers = libstac.set_request_headers(settings)

    # Connect to STAC API
    stac_helper = libstac.STACHelper()
    stac_helper.connect_to_stac(client_url, req_headers)
    stac_helper.conforms_to_collections()

    if collection_id:
        collection_dict = stac_helper.get_collection(collection_id)

        if format == "plain":
            if basic_info:
                return libstac.print_basic_collection_info(collection_dict)
            return libstac.print_summary(collection_dict)
        else:
            if pretty_print:
                output = StringIO()
                pprint(collection_dict, stream=output)
                sys.stdout.write(output.getvalue())
            else:
                json_output = json.dumps(collection_dict)
                sys.stdout.write(json_output)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
