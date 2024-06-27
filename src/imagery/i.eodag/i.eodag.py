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
# % description: Downloads imagery datasets from various providers through the EODAG API.
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
# % description: List filtered products and exit
# %end

# %flag
# % key: j
# % description: Print extended metadata information in JSON style
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
# % key: area_relation
# % type: string
# % description: Spatial relation of footprint to AOI
# % options: Intersects,Contains,IsWithin
# % required: no
# % guisection: Region
# %end

# %option
# % key: minimum_overlap
# % type: integer
# % description: Minimal AOI area covered by the scene [0, 100]
# % required: no
# % guisection: Region
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
# % label: The provider to search within.
# % description: Providers available by default: https://eodag.readthedocs.io/en/stable/getting_started_guide/providers.html
# % required: no
# % guisection: Filter
# %end

# %option
# % key: sort
# % description: Field to sort values by
# % multiple: yes
# % options: ingestiondate,cloudcover
# % answer: cloudcover,ingestiondate
# % guisection: Sort
# %end

# %option
# % key: order
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: asc
# % guisection: Sort
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
# % key: save
# % type: string
# % description: File name to save in (the format will be adjusted according to the file extension)
# % label: Supported files extensions [geojson: Rreadable by i.eodag | json: Beautified]
# % guisection: Filter
# %end

# %rules
# % exclusive: file, id
# % exclusive: -l, -j
# %end


import sys
import os
import getpass
import pytz
import json
from pathlib import Path
from subprocess import PIPE
from datetime import datetime, timedelta, timezone
from functools import cmp_to_key

import grass.script as gs
from grass.pygrass.modules import Module


def create_dir(directory):
    """Creates directory."""
    try:
        Path(directory).mkdir(parents=True, exist_ok=True)
    except:
        gs.fatal(_("Could not create directory {}").format(directory))


def get_bb(proj):
    """Gets the bounding box of the current computational
    region in geographic coordinates.

    :param proj: Projection information from 'gs.parse_command("g.proj", flags="j")'
    :type proj: str

    :return: Bounding box of the current computational region.
             Format:
             {"lonmin" : lonmin, "latmin" : latmin,
             "lonmax" : lonmax, "latmax" : latmax}
    :rtype: dict
    """
    gs.verbose("Generating AOI from bounding box...")
    if proj["+proj"] != "longlat":
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
    """Parses and returns the AOI.

    :param vector: Vector map (if None, returns the boudning box)
    :type vector: str

    :return: Either a WKT when using a Vector map, or a dict representing
             the current computational region bounding box.
             The latter format:
             {"lonmin" : lonmin, "latmin" : latmin,
             "lonmax" : lonmax, "latmax" : latmax}
    :rtype: str | dict
    """

    proj = gs.parse_command("g.proj", flags="j")
    if "+proj" not in proj:
        gs.fatal(_("Unable to get AOI: unprojected location not supported"))

    # Handle empty AOI
    if not vector:
        return get_bb(proj)

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

    geom_dict = gs.parse_command("v.out.ascii", format="wkt", **args)
    num_vertices = len(str(geom_dict.keys()).split(","))
    geom = [key for key in geom_dict][0]
    if proj["+proj"] != "longlat":
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
    """Search for products based on their ids.

    :param products_ids: List of products' ids.
    :type products_ids: list

    :return: EO products found by searching with 'search_parameters'
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    gs.verbose("Searching for products...")
    search_result = []
    for query_id in products_ids:
        gs.verbose(_("Searching for {}".format(query_id)))
        product, count = dag.search(id=query_id, provider=options["provider"] or None)
        if count > 1:
            gs.warning(
                _("{}\nCould not be uniquely identified. Skipping...".format(query_id))
            )
        elif count == 0 or not product[0].properties["id"].startswith(query_id):
            gs.warning(_("{}\nNot Found. Skipping...".format(query_id)))
        else:
            gs.verbose(_("Found."))
            search_result.append(product[0])
    return SearchResult(search_result)


def setup_environment_variables(env, **kwargs):
    """Sets the eodag environment variables based on the provided options/flags.

    :param kwargs: options/flags from gs.parser
    :type kwargs: dict
    """
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
                    "Ignoring 'e' flag... \
                    'extract' option in the config file will be used. \
                    If you wish to use the 'e' flag, please specify a provider."
                )
            )
        if delete_archive:
            gs.warning(
                _(
                    "Ignoring 'd' flag... \
                    'delete_archive' option in the config file will be used. \
                    If you wish to use the 'd' flag, please specify a provider."
                )
            )
        if output:
            gs.warning(
                _(
                    "Ignoring 'output' option... \
                    'output' option in the config file will be used. \
                    If you wish to use the 'output' option, please specify a provider."
                )
            )


def normalize_time(datetime_str: str):
    """Unifies the different ISO formats into 'YYYY-MM-DDTHH:MM:SS'

    :param datetime_str: Datetime in ISO format
    :type datetime_str: str

    :return: Datetime converted to 'YYYY-MM-DDTHH:MM:SS'
    :rtype: str
    """
    normalized_datetime = datetime.fromisoformat(datetime_str)
    if normalized_datetime.tzinfo is None:
        normalized_datetime = normalized_datetime.replace(tzinfo=timezone.utc)
    # Remove microseconds
    normalized_datetime = normalized_datetime.replace(microsecond=0)
    # Convert time to UTC
    normalized_datetime = normalized_datetime.astimezone(pytz.utc)
    # Remove timezone info
    normalized_datetime = normalized_datetime.replace(tzinfo=None)
    return normalized_datetime.isoformat()


def no_fallback_search(search_parameters, provider):
    """Search in only one provider (fallback is disabled).

    :param search_parameters: Queryables to which searching will take place
    :type search_parameters: dict

    :param provider: Provider to use for searching
    :type provider: str

    :return: EO products found by searching with 'search_parameters'
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
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
    #       the pages manually, and look for the product themselves?
    try:
        # Merging the pages into one list with all products
        return SearchResult([j for i in search_result for j in i])
    except Exception as e:
        gs.debug(e)
        gs.fatal(_("Server error, please try again."))


def list_products(products):
    """Lists products on the Standard Output stream (shell).

    :param products: EO poducts to be listed
    :type products: class:'eodag.api.search_result.SearchResult'
    """
    columns = ["id", "publicationDate", "cloudCover", "productType"]
    columns_NA = ["id_NA", "time_NA", "cloudCover_NA", "productType_NA"]
    for product in products:
        product_line = ""
        for i, column in enumerate(columns):
            product_attribute_value = product.properties[column]
            # Display NA if not available
            if product_attribute_value is None:
                product_attribute_value = columns_NA[i]
            else:
                if column == "cloudCover":
                    # Special formatting for cloud cover
                    product_attribute_value = f"{product_attribute_value:2.0f}%"
                elif column == "publicationDate":
                    # Special formatting for datetime
                    try:
                        product_attribute_value = normalize_time(
                            product_attribute_value
                        )
                    except:
                        product_attribute_value = product.properties[column]
            if i != 0:
                product_line += " "
            product_line += product_attribute_value
        print(product_line)


def list_products_json(products):
    """Lists products on the Standard Output stream (shell) in JSON format.

    :param products: EO poducts to be listed
    :type products: class:'eodag.api.search_result.SearchResult'
    """
    print(json.dumps(products.as_geojson_object(), indent=4))


def remove_duplicates(search_result):
    """Removes duplicated products, in case a provider returns a product multiple times."""
    filtered_result = []
    is_added = set()
    for product in search_result:
        if product.properties["id"] in is_added:
            continue
        is_added.add(product.properties["id"])
        filtered_result.append(product)
    return SearchResult(filtered_result)


def dates_to_iso_format():
    """Converts the start/end options to the isoformat and save them in-place.

    If options['end'] is not set, options['end'] will be today's date.
    If options['start'] is not set, options['start'] will be 60 days prior
    to options['end'] date.
    """
    end_date = options["end"]
    if not options["end"]:
        end_date = datetime.now(timezone.utc).isoformat()
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
    options["start"] = start_date
    options["end"] = end_date


def filter_result(search_result, geometry, **kwargs):
    """Filter results to comply with options/flags.
    :param search_result: Search Result to filter
    :type search_result: class:'eodag.api.search_result.SearchResult'

    :param geometry: WKT String with the geometry to filter with respect to
    :type geometry: str, optional

    :param kwargs: options/flags from gs.parser, with the crietria that will
                    be used for filtering.
    :type kwargs: dict

    :returns: A collection of EO products matching the filters criteria.
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    prefilter_count = len(search_result)
    area_relation = kwargs["area_relation"]
    minimum_overlap = kwargs["minimum_overlap"]
    cloud_cover = kwargs["clouds"]
    start_date = kwargs["start"]
    end_date = kwargs["end"]

    # If neither a geometry is provided as a parameter
    # nor a vector map is provided through "options",
    # then none of the geometry filtering will take place.
    if geometry is None and (area_relation is not None or minimum_overlap is not None):
        geometry = get_aoi(kwargs["map"])
    gs.verbose(_("Filtering results..."))

    if area_relation:
        # Product's geometry intersects with AOI
        if area_relation == "Intersects":
            search_result = search_result.filter_overlap(
                geometry=geometry, intersects=True
            )
        # Product's geometry contains the AOI
        elif area_relation == "Contains":
            search_result = search_result.filter_overlap(
                geometry=geometry, contains=True
            )
        # Product's geometry is within the AOI
        elif area_relation == "IsWithin":
            search_result = search_result.filter_overlap(geometry=geometry, within=True)

    if minimum_overlap:
        # Percentage of the AOI area covered by the product's geometry
        search_result = search_result.filter_overlap(
            geometry=geometry, minimum_overlap=int(minimum_overlap)
        )

    if cloud_cover:
        search_result = search_result.filter_property(
            operator="le", cloudCover=int(cloud_cover)
        )

    search_result = search_result.filter_date(start=start_date, end=end_date)
    search_result = remove_duplicates(search_result)

    postfilter_count = len(search_result)
    gs.verbose(
        _("{} product(s) filtered out.".format(prefilter_count - postfilter_count))
    )

    return search_result


def sort_result(search_result):
    """Sorts search results according to options['sort'] and options['order']

    options['sort'] parameters and options['order'] are matched correspondingly.
    If options['order'] parameters are not suffcient,
    'asc' will be used by default.

    :param search_result: EO products to be sorted
    :type search_result: class'eodag.api.search_result.SearchResult'

    :return: Sorted EO products
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    gs.verbose(_("Sorting..."))

    sort_keys = options["sort"].split(",")
    sort_order = options["order"]

    # Sort keys and sort orders are matched respectively
    def products_compare(first, second):
        for sort_key in sort_keys:
            if sort_key == "ingestiondate":
                first_value = first.properties["publicationDate"]
                second_value = second.properties["publicationDate"]
            elif sort_key == "cloudcover":
                first_value = first.properties["cloudCover"]
                second_value = second.properties["cloudCover"]
            if first_value < second_value:
                return 1 if sort_order == "desc" else -1
            elif first_value > second_value:
                return -1 if sort_order == "desc" else 1
        return 0

    search_result.sort(key=cmp_to_key(products_compare))
    return search_result


def save_search_result(search_result, file_name):
    """Save search results to files.

    If the file is a json file,
    the search result is saved in a beautified JSON format.
    If the file is a geojson file,
    the search result is saved using EODAG serialize method,
    saving it in a format that can be read again by i.eodag,
    to restore the search results.

    :param search_result: EO products to be sorted
    :type search_result: class'eodag.api.search_result.SearchResult'

    :param file_name: EO products to be sorted
    :type file_name: str
    """
    if file_name[-5:].lower() == ".json":
        gs.verbose(_("Saving searchin result in '{}'".format(file_name)))
        with open(file_name, "w") as f:
            f.write(
                json.dumps(
                    search_result.as_geojson_object(), ensure_ascii=False, indent=4
                )
            )
    if file_name[-8:].lower() == ".geojson":
        gs.verbose(_("Saving searchin result in '{}'".format(file_name)))
        dag.serialize(search_result, filename=file_name)


def main():
    # Products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    global dag
    setup_environment_variables(os.environ, **options, **flags)
    dag = EODataAccessGateway()
    if options["provider"]:
        dag.set_preferred_provider(options["provider"])

    dates_to_iso_format()

    # Download by IDs
    # Searching for additional products will not take place
    ids_set = set()
    if options["id"]:
        # Parse IDs
        ids_set = set(pid.strip() for pid in options["id"].split(","))
    elif options["file"]:
        # Read IDs from file
        if Path(options["file"]).is_file():
            gs.verbose(_('Reading file "{}"'.format(options["file"])))
            ids_set = set(
                Path(options["file"]).read_text(encoding="UTF8").strip().split("\n")
            )
        else:
            gs.fatal(_('Could not open file "{}"'.format(options["file"])))

    if len(ids_set):
        # Remove empty string
        ids_set.discard(str())
        gs.message(_("Found {} distinct ID(s).".format(len(ids_set))))
        gs.message("\n".join(ids_set))

        # Search for products found from options["file"] or options["id"]
        search_result = search_by_ids(ids_set)
    else:
        items_per_page = 40
        # TODO: Check that the product exists,
        # could be handled by catching exceptions when searching...
        product_type = options["dataset"]

        # HARDCODED VALUES FOR TESTING { "lonmin": 1.9, "latmin": 43.9, "lonmax": 2, "latmax": 45, }
        geometry = get_aoi(options["map"])
        gs.verbose(_("AOI: {}".format(geometry)))

        search_parameters = {
            "items_per_page": items_per_page,
            "productType": product_type,
            "geom": geometry,
        }

        if options["clouds"]:
            search_parameters["cloudCover"] = options["clouds"]

        search_parameters["start"] = options["start"]
        search_parameters["end"] = options["end"]
        if options["provider"]:
            search_result = no_fallback_search(search_parameters, options["provider"])
        else:
            search_result = dag.search_all(**search_parameters)

    search_result = filter_result(
        search_result, geometry if "geometry" in locals() else None, **options
    )
    search_result = sort_result(search_result)
    print(type(search_result))

    gs.message(_("{} product(s) found.").format(len(search_result)))
    # TODO: Add a way to search in multiple providers at once
    #       Check for when this feature is added https://github.com/CS-SI/eodag/issues/163
    if options["save"]:
        save_search_result(search_result, options["save"])
    if flags["l"]:
        list_products(search_result)
    elif flags["j"]:
        list_products_json(search_result)
    else:
        # TODO: Consider adding a quicklook flag
        # TODO: Add timeout and wait parameters for downloading offline products...
        # https://eodag.readthedocs.io/en/stable/getting_started_guide/product_storage_status.html
        dag.download_all(search_result)


if __name__ == "__main__":
    gs.warning(_("Experimental Version..."))
    gs.warning(
        _(
            "This module is still under development, \
            and its behaviour is not guaranteed to be reliable"
        )
    )
    options, flags = gs.parser()

    try:
        from eodag import EODataAccessGateway
        from eodag import setup_logging
        from eodag.api.search_result import SearchResult
    except:
        gs.fatal(_("Cannot import eodag. Please intall the library first."))

    # To disable eodag logs, set DEBUG to 0
    # with " g.gisenv 'set=DEBUG=0' "
    if "DEBUG" in gs.read_command("g.gisenv"):
        debug_level = int(gs.read_command("g.gisenv", get="DEBUG"))
        if not debug_level:
            setup_logging(1)
        elif debug_level == 1:
            setup_logging(2)
        else:
            setup_logging(3)

    sys.exit(main())
