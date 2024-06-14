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

# FLAGS
# %flag
# % key: l
# % description: List the search result without downloading
# %end

# %flag
# % key: e
# % description: Extract the downloaded the datasets, not considered unless provider is set
# %end

# %flag
# % key: d
# % description: Delete the product archive after downloading, not considered unless provider is set
# %end

# OPTIONS
# %option
# % key: dataset
# % type: string
# % description: Imagery dataset to search for
# % required: no
# % answer: S2_MSI_L1C
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
# % description: Maximum cloud cover percentage for scene [0, 100]
# % required: no
# % guisection: Filter
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
# % multiple: no
# % description: Text file with a collection of IDs, one ID per line
# % guisection: Filter
# %end

# %option
# % key: provider
# % type: string
# % description: The provider to search within. Providers available by default: https://eodag.readthedocs.io/en/stable/getting_started_guide/providers.html
# % required: no
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

# %rules
# % exclusive: file, id
# %end


import sys
import os
import getpass
from pathlib import Path
from subprocess import PIPE
from datetime import datetime, timedelta

import grass.script as gs
from grass.pygrass.modules import Module
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

    args = {}
    args["input"] = vector

    if gs.vector_info_topo(vector)["areas"] <= 0:
        gs.fatal(_("No areas found in AOI map <{}>...").format(vector))
    elif gs.vector_info_topo(vector)["areas"] > 1:
        gs.warning(
            _(
                "More than one area found in AOI map <{}>. \
                      Using only the first area..."
            ).format(vector)
        )

    # are we in LatLong location?
    s = gs.read_command("g.proj", flags="j")
    kv = gs.parse_key_val(s)
    if "+proj" not in kv:
        gs.fatal(_("Unable to get AOI: unprojected location not supported"))

    geom_dict = gs.parse_command("v.out.ascii", format="wkt", **args)
    num_vertices = len(str(geom_dict.keys()).split(","))
    geom = [key for key in geom_dict][0]
    if kv["+proj"] != "longlat":
        gs.verbose(
            _("Generating WKT from AOI map ({} vertices)...").format(num_vertices)
        )
        # TODO: Might need to check for number of coordinates
        #       Make sure it won't cause problems like in:
        #       https://github.com/OSGeo/grass-addons/blob/grass8/src/imagery/i.sentinel/i.sentinel.download/i.sentinel.download.py#L273
        feature_type = geom[: geom.find("(")]
        coords = geom.replace(feature_type + "((", "").replace("))", "").split(", ")
        projected_geom = feature_type + "(("
        coord_proj = Module(
            "m.proj",
            input="-",
            flags="od",
            stdin_="\n".join(coords),
            stdout_=PIPE,
            stderr_=PIPE,
        )
        projected_geom += (", ").join(
            [
                " ".join(poly_coords.split("|")[0:2])
                for poly_coords in coord_proj.outputs["stdout"]
                .value.strip()
                .split("\n")
            ]
        ) + "))"
        return projected_geom
    return geom


def search_by_ids(products_ids):
    gs.message("Searching for products...")
    search_result = []
    for query_id in products_ids:
        gs.message(_("Searching for {}".format(query_id)))
        if options["provider"]:  # If provider is set, then search without fallback
            product, count = dag.search(id=query_id, provider=options["provider"])
        else:
            product, count = dag.search(id=query_id)
        if count > 1:
            gs.message(_("Could not be uniquely identified."))
        elif count == 0 or not product[0].properties["id"].startswith(query_id):
            gs.message(_("Not found."))
        else:
            gs.message(_("Found."))
            search_result.append(product[0])
    return search_result


def setup_environment_variables(env, **kwargs):
    provider = kwargs.get("provider")
    extract = kwargs.get("e")
    delete_archive = kwargs.get("d")
    output = kwargs.get("output")
    config = kwargs.get("config")

    # Setting the envirionmnets variables has to come before the eodag initialization
    if config:
        env["EODAG_CFG_FILE"] = options["config"]
    if provider:
        # Flags can't be taken into consideration without specifying the provider
        env[f"EODAG__{provider.upper()}__DOWNLOAD__EXTRACT"] = str(extract)
        env[f"EODAG__{provider.upper()}__DOWNLOAD__DELETE_ARCHIV"] = str(delete_archive)
        if output:
            env[f"EODAG__{provider.upper()}__DOWNLOAD__OUTPUTS_PREFIX"] = output
    else:
        if extract:
            gs.warning(
                _(
                    """Ignoring 'e' flag...
                    'extract' option in the config file will be used.
                    If you wish to use the 'e' flag, please specify a provider."""
                )
            )
        if delete_archive:
            gs.warning(
                _(
                    """Ignoring 'd' flag...
                    'delete_archive' option in the config file will be used.
                    If you wish to use the 'd' flag, please specify a provider."""
                )
            )
        if output:
            gs.warning(
                _(
                    """Ignoring 'output' option...
                    'output' option in the config file will be used.
                    If you wish to use the 'output' option, please specify a provider."""
                )
            )


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


def list_products(products):
    df = create_products_dataframe(products)
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


def apply_filters(search_result):
    filtered_result = []
    for product in search_result:
        valid = True
        if (
            options["clouds"]
            and "cloudCover" in product.properties
            and product.properties["cloudCover"] is not None
            and product.properties["cloudCover"] > int(options["clouds"])
        ):
            valid = False
        if valid:
            filtered_result.append(product)
    return filtered_result


def main():
    # Products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    global dag
    setup_environment_variables(os.environ, **options, **flags)
    dag = EODataAccessGateway()
    if options["provider"]:
        dag.set_preferred_provider(options["provider"])

    # Download by IDs
    # Searching for additional products won't take place
    ids_set = set()
    if options["id"]:
        # Parse IDs
        ids_set = set(pid.strip() for pid in options["id"].split(","))
    elif options["file"]:
        # Read IDs from file
        if Path(options["file"]).is_file():
            gs.message(_('Reading file "{}"'.format(options["file"])))
            ids_set = set(
                Path(options["file"]).read_text(encoding="UTF8").strip().split("\n")
            )
        else:
            gs.fatal(_('Could not open file "{}"'.format(options["file"])))

    if len(ids_set):
        ids_set.discard(str())
        gs.message(_("Found {} distinct ID(s).".format(len(ids_set))))
        gs.message("\n".join(ids_set))
        search_result = search_by_ids(ids_set)
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
        if options["provider"]:
            search_result = no_fallback_search(search_parameters, options["provider"])
        else:
            search_result = dag.search_all(**search_parameters)

    gs.message(_("Applying filters..."))
    search_result = apply_filters(search_result)
    gs.message(_("{} product(s) found.").format(len(search_result)))
    if flags["l"]:
        list_products(search_result)
    else:
        # TODO: Consider adding a quicklook flag
        # TODO: Add timeout and wait parameters for downloading offline products...
        # https://eodag.readthedocs.io/en/stable/getting_started_guide/product_storage_status.html
        dag.download_all(search_result)


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
