#!/usr/bin/env python3

############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Downloads imagery datasets e.g. Landsat, Sentinel, and MODIS
#              using EODAG API.
# COPYRIGHT:   (C) 2024-2025 by Hamed Elgizery, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################


# %Module
# % description: Eodag interface to install imagery datasets from various providers.
# % keyword: imagery
# % keyword: eodag
# % keyword: sentinel
# % keyword: landsat
# % keyword: modis
# % keyword: datasets
# % keyword: download
# %end

# %option
# % key: dataset
# % type: string
# % description: Imagery dataset to search for
# % required: yes
# % answer: S1_SAR_GRD
# % guisection: Filter
# %end

# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded data OR search results
# % required: no
# % guisection: Output
# %end

# %option
# % key: format
# % type: string
# % description: Output format
# % required: no
# % options: plain,json
# % answer: json
# %end

# %option G_OPT_F_INPUT
# % key: config
# % label: Full path to yaml config file, following the format https://eodag.readthedocs.io/en/stable/getting_started_guide/configure.html#yaml-user-configuration-file
# % description: '-' for standard input
# % required: no
# %end

# %option
# % key: id
# % type: string
# % multiple: yes
# % description: List of scenes IDs to download
# % guisection: Filter
# %end

# %option
# % key: provider
# % type: string
# % description: Provider to use for searching/downloading, if none is provided the searching will be done according to the config file priority
# % required: yes
# % guisection: Filter
# %end

# %option
# % key: start
# % type: string
# % description: Start date (in any ISO 8601 format), by default it is 60 days ago
# % guisection: Filter
# %end

# %option
# % key: end
# % type: string
# % description: End date (in any ISO 8601 format)
# % guisection: Filter
# %end

# %option
# % key: relation
# % type: string
# % description: Relation with area of interest
# % options: intersects, contains, within
# % answer: intersects
# % guisection: Optional
# %end

# %option
# % key: clouds
# % type: integer
# % description: Maximum cloud cover percentage for Landsat scene
# % required: no
# % guisection: Filter
# %end

# %option
# % key: timeout
# % type: integer
# % description: Download timeout in seconds
# % answer: 300
# % guisection: Optional
# %end


# %flag
# % key: l
# % description: List the search result without downloading
# %end

# %flag
# % key: e
# % description: Extract the downloaded the datasets
# %end

# %flag
# % key: d
# % description: Delete the product archieve after downloading
# %end


import sys
import os
import getpass
from datetime import *
import grass.script as gs
from grass.exceptions import ParameterError
from pathlib import Path


def create_dir(directory):
    try:
        p = Path(directory).mkdir(parents=True, exist_ok=True)
    except Exception as e:
        gs.fatal(_("Could not create directory {}").format(dir))


def get_bb(vector=None):
    args = {}
    if vector:
        args["vector"] = vector
    # are we in LatLong location?
    kv = gs.parse_command("g.proj", flags="j")
    if "+proj" not in kv:
        gs.fatal(_("Unable to get bounding box: unprojected location not supported"))
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg", **args)
        return {
            "lonmin": info["nw_long"],
            "latmin": info["sw_lat"],
            "lonmax": info["ne_long"],
            "latmax": info["nw_lat"],
        }
    info = gs.parse_command("g.region", flags="upg", **args)
    return {
        "lonmin": info["w"],
        "latmin": info["s"],
        "lonmax": info["e"],
        "latmax": info["n"],
    }


def download_products(products_list):
    dag.download_all(products_list)


def download_by_id(query_id: str):
    gs.verbose(
        _(
            "Searching for product ending with: {}".format(
                query_id[-min(len(query_id), 8) :]
            )
        )
    )
    product, count = dag.search(id=query_id)
    if count != 1:
        raise ParameterError("Product couldn't be uniquely identified")
    if not product[0].properties["id"].startswith(query_id):
        raise ParameterError("Product wasn't found")
    gs.verbose(
        _("Poduct ending with: {} is found.".format(query_id[-min(len(query_id), 8) :]))
    )
    gs.verbose(_("Downloading..."))
    dag.download(product[0])


def download_by_ids(products_ids: list):
    for product_id in products_ids:
        try:
            download_by_id(product_id)
        except ParameterError:
            gs.error(
                _(
                    "Product ending with: {}, failed to download".format(
                        id[-min(len(id), 8) :]
                    )
                )
            )


def setup_environment_variables():
    os.environ["EODAG__{}__DOWNLOAD__EXTRACT".format(options["provider"])] = str(
        flags["e"]
    )
    os.environ["EODAG__{}__DOWNLOAD__DELETE_ARCHIV".format(options["provider"])] = str(
        flags["d"]
    )

    if options["output"]:
        os.environ[
            "EODAG__{}__DOWNLOAD__OUTPUTS_PREFIX".format(options["provider"])
        ] = options["output"]

    if options["config"]:
        os.environ["EODAG_CFG_FILE"] = options["config"]


def normalize_time(datetime_str: str):
    normalized_datetime = datetime.fromisoformat(datetime_str)
    normalized_datetime = normalized_datetime.replace(microsecond=0)
    normalized_datetime = normalized_datetime.replace(tzinfo=None)
    return normalized_datetime.isoformat()


def no_fallback_search(search_parameters, provider):
    try:
        server_poke = dag.search(**search_parameters, provider=provider)
        if server_poke[1] == 0:
            gs.verbose(_("No products found"))
            return SearchResult([])
    except Exception as e:
        gs.verbose(e)
        gs.fatal(_("Server error, try again."))

    # https://eodag.readthedocs.io/en/stable/api_reference/core.html#eodag.api.core.EODataAccessGateway.search_iter_page
    # This will use the prefered provider by default
    search_result = dag.search_iter_page(**search_parameters)

    # TODO: Would it be useful if user could iterate through the pages manually, and look for the product themselves?
    try:
        return list(search_result)[0]
    except Exception as e:
        gs.verbose(e)
        gs.fatal(_("Server error, try again."))


def main():
    # products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    # setting the envirionmnets variables has to come before the dag initialization
    setup_environment_variables()

    global dag
    dag = EODataAccessGateway()

    if options["provider"]:
        dag.set_preferred_provider(options["provider"])

    # Download by ids... if ids are provided only these ids will be downloaded
    if options["id"]:
        ids = options["id"].split(",")
        download_by_ids(ids)
    else:

        items_per_page = 20
        # TODO: Check that the product exists, could be handled by catching exceptions when searching...
        product_type = options["dataset"]

        # TODO: Allow user to specify a shape file path
        geom = (
            # use boudning box of current computational region
            # get_bb()
            {
                "lonmin": 1.9,
                "latmin": 43.9,
                "lonmax": 2,
                "latmax": 45,
            }  # hardcoded for testing
        )

        gs.verbose(geom)

        search_parameters = {
            "items_per_page": items_per_page,
            "productType": product_type,
            # TODO: Convert to a shapely object
            "geom": geom,
        }

        if options["clouds"]:
            search_parameters["cloudCover"] = options["clouds"]

        # Assumes that the user enter time in UTC
        end_date = options["end"]
        if not options["end"]:
            end_date = datetime.utcnow().isoformat()
        try:
            end_date = normalize_time(end_date)
        except Exception as e:
            gs.debug(e)
            gs.fatal(_("Could not parse 'end' time."))

        start_date = options["start"]
        if not options["start"]:
            delta_days = timedelta(60)
            start_date = (datetime.fromisoformat(end_date) - delta_days).isoformat()
        try:
            start_date = normalize_time(start_date)
        except Exception as e:
            gs.debug(e)
            gs.fatal(_("Could not parse 'start' time."))

        if end_date < start_date:
            gs.fatal(
                _(
                    "End Date ({}) can not come before Start Date ({})".format(
                        end_date, start_date
                    )
                )
            )

        # TODO: Requires further testing to make sure the isoformat works with all the providers
        search_parameters["start"] = start_date
        search_parameters["end"] = end_date

        search_results = no_fallback_search(search_parameters, options["provider"])
        num_results = len(search_results)

        gs.verbose(
            _("Found {} matching scenes of type {}".format(num_results, product_type))
        )
        if flags["l"]:
            # TODO: Oragnize output format better
            idx = 0
            for product in search_results:
                print(
                    _(
                        "Product #{} - ID:{},provider:{}".format(
                            idx, product.properties["id"], product.provider
                        )
                    )
                )
                idx += 1
        else:
            # TODO: Consider adding a quicklook flag
            # TODO: Add timeout and wait parameters for downloading offline products...
            # https://eodag.readthedocs.io/en/stable/getting_started_guide/product_storage_status.html
            download_products(search_results)


if __name__ == "__main__":
    options, flags = gs.parser()
    try:
        from eodag import EODataAccessGateway
        from eodag import setup_logging
        from eodag.api.search_result import SearchResult

        debug_level = int(gs.read_command("g.gisenv", get="DEBUG"))
        if not debug_level:
            setup_logging(1)
        elif debug_level == 1:
            setup_logging(2)
        else:
            setup_logging(3)
    except:
        gs.fatal(_("Cannot import eodag. Please intall the library first."))

    sys.exit(main())
