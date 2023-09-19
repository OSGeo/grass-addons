#!/usr/bin/env python3

############################################################################
#
# MODULE:       t.stac.import
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Import data into GRASS from SpatioTemporal Asset Catalogs (STAC) APIs.
# COPYRIGHT:    (C) 2023 Corey White
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
# %end

# %option
# % key: url
# % type: string
# % answer: https://earth-search.aws.element84.com/v1/
# % description: STAC API Client URL (examples at https://stacspec.org/en/about/datasets/ )
# % required: yes
# %end

# %flag
# % key: c
# % description: Get the avaliable collections then exit
# % guisection: Request
# %end

# %flag
# % key: i
# % description: Get the avaliable items from collections then exit
# % guisection: Request
# %end

# %flag
# % key: r
# % description: Reproject raster data using r.import if needed
# %end

#%option
#% key: collections
#% type: string
#% required: no
#% multiple: yes
#% description: List of one or more Collection IDs or pystac.Collection instances. Only Items in one of the provided Collections will be searched
#% guisection: Request
#%end

# %option
# % key: max_items
# % type: integer
# % description:  The maximum number of items to return from the search, even if there are more matching results.
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
# % answer: 100
# % guisection: Request
# %end

# %option
# % key: bbox
# % type: string
# % required: no
# % description: The bounding box of the request (example [-72.5,40.5,-72,41])
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

# %option
# % key: region
# % type: double
# % label: Import subregion only (default is current region)
# % description: Format: xmin,ymin,xmax,ymax - usually W,S,E,N
# % key_desc: xmin,ymin,xmax,ymax
# % multiple: no
# % required: no
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
# % answer: bilinear_f
# %end

# %option
# % key: resolution
# % type: double
# % required: no
# % multiple: no
# % description: Resolution of output raster map (required if location projection not longlat)
# % guisection: Output
# %end

# %option
# % key: memory
# % type: integer
# % required: no
# % multiple: no
# % label: Maximum memory to be used (in MB)
# % description: Cache size for raster rows
# % answer: 300
# %end

import os
import sys
import base64
import subprocess
from pystac_client import Client
import grass.script as gs

try:
    from pystac_client import Client
except ImportError:
    from pystac_client import Client


def get_region_params(self, opt_region):
    """Get region parameters from region specified or active default region

    @return region_params as a dictionary
    """

    if opt_region:
        reg_spl = opt_region.strip().split("@", 1)
        reg_mapset = "."
        if len(reg_spl) > 1:
            reg_mapset = reg_spl[1]

    if opt_region:
        s = gs.read_command("g.region", quiet=True, flags="ug", region=opt_region)
        region_params = gs.parse_key_val(s, val_type=float)
        gs.verbose("Using region parameters for region %s" % opt_region)
    else:
        region_params = gs.region()
        gs.verbose("Using current grass region")

    return region_params


def compute_bbox(self):
    """Get extent for WCS query (bbox) from region parameters

    @return bounding box defined by list [minx,miny,maxx,maxy]
    """
    boundingboxvars = ("w", "s", "e", "n")
    boundingbox = list()
    for f in boundingboxvars:
        boundingbox.append(self.params["region"][f])
    gs.verbose(
        "Boundingbox coordinates:\n %s  \n [West, South, Eest, North]" % boundingbox
    )
    return boundingbox


def validate_collections_option(client, collections=[]):
    """Validate that the collection the user specificed is valid

    Args:
        collections (String[]): User defined collection
        client (Client): A PyStac Client

    Returns:
        boolean: Returns true if the collection is avaliable.
    """
    avaliable_collections = client.get_collections()
    if collections in avaliable_collections:
        return True
    gs.warning(_("The specified collections do not exisit."))

    for collection in avaliable_collections:
        gs.warning(_(f"{collection} collection found"))

    return False


def search_stac_api(client, **kwargs):
    """Search the STAC API"""
    search = client.search(**kwargs)
    gs.message(_(f"{search.matched()} items found"))
    return search


def fetch_asset():
    """Fetch Asset"""
    pass


def get_all_collections(client):
    """Get a list of collections from STAC Client"""
    collections = client.get_collections()
    collection_list = list(collections)
    gs.message(_(f"{len(collection_list)} collections found:"))
    for i in collection_list:
        gs.message(_(i.id))
    return collection_list


def get_collection_items(client, collection_name):
    """Get collection"""
    collection = client.get_collection(collection_name)
    gs.message(_(f"Collection: {collection.title}"))
    gs.message(_(f"Description: {collection.description}"))
    gs.message(_(f"Spatial Extent: {collection.extent.spatial.bboxes}"))
    gs.message(_(f"Temporal Extent: {collection.extent.temporal.intervals}"))
    gs.message(_(f"License: {collection.license}"))
    return collection

    # items = collection.get_all_items()
    # gs.message(_(len(list(items))))
    # return items
    # for i in items:
    #     gs.message(_(i.id))


def main():
    """Main function"""

    client_url = options["url"]
    ids = options["ids"]  # optional
    collections = options["collections"]  # Maybe limit to one?
    limit = options["limit"]  # optional
    max_items = options["max_items"]  # optional
    bbox = options["bbox"]  # optional
    intersects = options["intersects"]  # optional
    datetime = options["datetime"]  # optional
    query = options["query"]  # optional
    filter = options["filter"]  # optional
    filter_lang = options["filter_lang"]  # optional

    client = Client.open(client_url)
    gs.message(_(f"Catalog: {client.title}"))

    collections_only = flags["c"]
    collection_itmes_only = flags["i"]

    if collections_only:
        collection_list = get_all_collections(client)
        return None

    if collection_itmes_only:
        collection_item_list = get_collection_items(client, collections)
        return None

    if validate_collections_option(client, collections):
        items = search_stac_api(
            client=client,
            ids=ids,
            limit=limit,
            max_items=max_items,
            bbox=bbox,
            intersects=intersects,
            datetime=datetime,
            query=query,
            filter=filter,
            filter_lang=filter_lang,
        )
        print(items)


if __name__ == "__main__":
    options, flags = gs.parser()
    sys.exit(main())
