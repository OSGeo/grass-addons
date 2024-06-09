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
# %option G_OPT_V_MAP
# % description: If not given then current computational extent is used
# % label: Name of input vector map to define Area of Interest (AOI)
# % required: no
# % guisection: Region
# %end
# %option
# % key: clouds
# % type: integer
# % description: Maximum cloud cover percentage for Sentinel scene
# % required: no
# % guisection: Filter
# %end
# %option G_OPT_V_OUTPUT
# % key: footprints
# % description: Name for output vector map with footprints
# % label: Only supported for download from ESA_Copernicus Open Access Hub
# % required: no
# % guisection: Output
# %end
# %option G_OPT_M_DIR
# % key: output
# % description: Name for output directory where to store downloaded data OR search results
# % required: no
# % guisection: Output
# %end
# %option G_OPT_F_INPUT
# % key: config
# % label: Full path to yaml config file
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
# % key: file
# % type: string
# % multiple: yes
# % description: List of text files with IDs to download
# % guisection: Filter
# %end
# %option
# % key: provider
# % type: string
# % description: Available providers: https://eodag.readthedocs.io/en/stable/getting_started_guide/providers.html
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
from pathlib import Path
from datetime import datetime, timedelta

import grass.script as gs
from grass.exceptions import ParameterError


def create_dir(directory):
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
    except:
        gs.fatal(_("Could not create directory {}").format(dir))


def get_bb():
    # are we in LatLong location?
    kv = gs.parse_command("g.proj", flags="j")
    if "+proj" not in kv:
        gs.fatal(_("Unable to get bounding box: unprojected location not supported"))
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg")
        return {
            "lonmin": info["nw_long"],
            "latmin": info["sw_lat"],
            "lonmax": info["ne_long"],
            "latmax": info["nw_lat"],
        }
    info = gs.parse_command("g.region", flags="upg")
    return {
        "lonmin": info["w"],
        "latmin": info["s"],
        "lonmax": info["e"],
        "latmax": info["n"],
    }


def get_aoi(vector=None):
    """Get the AOI for querying"""
    # Handle empty AOI
    if not vector:
        return get_bb()

    # TODO: Read Vector WKB


def download_by_id(query_id: str):
    gs.message(_("Attempting to download product: {}".format(query_id)))
    product, count = dag.search(id=query_id, provider=options["provider"])
    if count != 1:
        raise ParameterError("Product couldn't be uniquely identified.")
    if not product[0].properties["id"].startswith(query_id):
        raise ParameterError("Product wasn't found.")
    gs.verbose(_("Poduct {} is found.".format(query_id)))
    gs.verbose(_("Downloading {}".format(query_id)))
    dag.download(product[0])


def ids_from_file_txt(ids_file_txt):
    ids_set = set()
    with open(ids_file_txt, "r") as ids_stream:
        line_index = 0
        lines = ids_stream.read().split("\n")
        for line in lines:
            line_index += 1
            if not line:
                continue
            line = line.strip()
            if line.find(" ") != -1:
                gs.warning(
                    _(
                        'File "{}", line {}, has space(s). Skipping line... '.format(
                            ids_file_txt, line_index
                        )
                    )
                )
                continue
            ids_set.add(line.strip())
    return ids_set


def download_by_ids(products_ids):
    # Search in all recognized providers
    for product_id in products_ids:
        try:
            download_by_id(product_id)
        except ParameterError as e:
            gs.error(e)
            gs.error(_("Product {} failed to download".format(product_id)))


def parse_id_option(id_option_string):
    to_download_ids = id_option_string.split(",")
    ids_set = set()
    for to_download_id in to_download_ids:
        ids_set.add(to_download_id.strip())
    return ids_set


def parse_file_option(file_option_string):
    ids_set = set()
    files_list = file_option_string.split(",")
    for file in files_list:
        try:
            ids_set.update(ids_from_file_txt(file))
        except FileNotFoundError:
            gs.warning(_('Couldn\'t read file "{}", Skipping file...'.format(file)))
    return ids_set


def setup_environment_variables():
    # Setting the envirionmnets variables has to come before the eodag initialization
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
        gs.fatal(_("Server error, please try again."))

    # https://eodag.readthedocs.io/en/stable/api_reference/core.html#eodag.api.core.EODataAccessGateway.search_iter_page
    # This will use the prefered provider by default
    search_result = dag.search_iter_page(**search_parameters)

    # TODO: Would it be useful if user could iterate through
    # the pages manually, and look for the product themselves?
    try:
        # Merging the pages into one list with all products
        return [j for i in search_result for j in i]
    except Exception as e:
        gs.verbose(e)
        gs.fatal(_("Server error, please try again."))


def create_products_dataframe(eo_products):
    result_dict = {"id": [], "time": [], "cloud_coverage": [], "product_type": []}
    for product in eo_products:
        if "id" in product.properties and product.properties["id"] is not None:
            result_dict["id"].append(product.properties["id"])
        else:
            result_dict["id"].append(None)
        if (
            "startTimeFromAscendingNode" in product.properties
            and product.properties["startTimeFromAscendingNode"] is not None
        ):
            try:
                result_dict["time"].append(
                    normalize_time(product.properties["startTimeFromAscendingNode"])
                )
            except:
                result_dict["time"].append(
                    product.properties["startTimeFromAscendingNode"]
                )
        else:
            result_dict["time"].append(None)
        if (
            "cloudCover" in product.properties
            and product.properties["cloudCover"] is not None
        ):
            result_dict["cloud_coverage"].append(product.properties["cloudCover"])
        else:
            result_dict["cloud_coverage"].append(None)
        if (
            "productType" in product.properties
            and product.properties["productType"] is not None
        ):
            result_dict["product_type"].append(product.properties["productType"])
        else:
            result_dict["product_type"].append(None)

    df = pd.DataFrame().from_dict(result_dict)
    return df


def main():
    # Products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    global dag
    setup_environment_variables()
    dag = EODataAccessGateway()
    if options["provider"]:
        dag.set_preferred_provider(options["provider"])
    else:
        # TODO: Add a way to search witout specifying a provider
        gs.fatal(_("Please specify a provider."))

    # Download by ids
    # Searching for additional products won't take place
    if options["id"] or options["file"]:
        # Duplicates will be
        ids_set = set()
        if options["id"]:
            ids_set.update(parse_id_option(options["id"]))
        if options["file"]:
            ids_set.update(parse_file_option(options["file"]))
        gs.message(_("Found {} distinct product(s) IDs.".format(len(ids_set))))
        for product_id in ids_set:
            gs.message(product_id)
        gs.verbose(_("Attempting to download."))
        download_by_ids(ids_set)
    else:
        items_per_page = 40
        # TODO: Check that the product exists,
        # could be handled by catching exceptions when searching...
        product_type = options["dataset"]

        # HARDCODED VALUES FOR TESTING { "lonmin": 1.9, "latmin": 43.9, "lonmax": 2, "latmax": 45, }  # hardcoded for testing

        geom = get_aoi(options["map"])
        gs.verbose(_("Region used for searching: {}".format(geom)))
        search_parameters = {
            "items_per_page": items_per_page,
            "productType": product_type,
            "geom": geom,
        }

        if options["clouds"]:
            search_parameters["cloudCover"] = options["clouds"]

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
        print(num_results)

        if flags["l"]:
            df = create_products_dataframe(search_results)
            gs.message(_("{} product(s) found.").format(num_results))
            for idx in range(len(df)):
                product_id = df["id"].iloc[idx]
                if product_id is None:
                    time_string = "id_NA"
                time_string = df["time"].iloc[idx]
                if time_string is None:
                    time_string = "time_NA"
                else:
                    time_string += "Z"
                cloud_cover_string = df["cloud_coverage"].iloc[idx]
                if cloud_cover_string is not None:
                    cloud_cover_string = f"{cloud_cover_string:2.0f}%"
                else:
                    cloud_cover_string = "cloudcover_NA"
                product_type = df["product_type"].iloc[idx]
                if product_type is None:
                    product_type = "producttype_NA"
                print(f"{product_id} {time_string} {cloud_cover_string} {product_type}")
        else:
            # TODO: Consider adding a quicklook flag
            # TODO: Add timeout and wait parameters for downloading offline products...
            # https://eodag.readthedocs.io/en/stable/getting_started_guide/product_storage_status.html
            dag.download_all(search_results)


if __name__ == "__main__":
    gs.warning(_("Experimental Version..."))
    gs.warning(
        _(
            "This module is still under development, and its behaviour is not guaranteed to be reliable"
        )
    )
    options, flags = gs.parser()

    try:
        from eodag import EODataAccessGateway
        from eodag import setup_logging
        from eodag.api.search_result import SearchResult
    except:
        gs.fatal(_("Cannot import eodag. Please intall the library first."))
    try:
        import pandas as pd
    except:
        gs.fatal(_("Cannot import pandas. Please intall the library first."))

    if "DEBUG" in gs.read_command("g.gisenv"):
        debug_level = int(gs.read_command("g.gisenv", get="DEBUG"))
        if not debug_level:
            setup_logging(1)
        elif debug_level == 1:
            setup_logging(2)
        else:
            setup_logging(3)

    sys.exit(main())
