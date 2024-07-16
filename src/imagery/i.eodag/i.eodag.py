#!/usr/bin/env python3

############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Downloads imagery secens e.g. Landsat, Sentinel, and MODIS
#              using EODAG API.
# COPYRIGHT:   (C) 2024-2025 by Hamed Elgizery, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

# %Module
# % description: Downloads imagery scenes from various providers through the EODAG API.
# % keyword: imagery
# % keyword: eodag
# % keyword: sentinel
# % keyword: landsat
# % keyword: modis
# % keyword: dataset
# % keyword: scene
# % keyword: download
# %end

# FLAGS
# %flag
# % key: l
# % description: List filtered products scenes and exit
# % guisection: Print
# %end

# %flag
# % key: j
# % description: Print scenes extended metadata information in JSON style and exit
# % guisection: Print
# %end

# OPTIONS
# %option
# % key: producttype
# % type: string
# % description: Imagery product type to search for
# % required: no
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
# % description: Name for output directory where to store downloaded scenes data
# % required: no
# % guisection: Output
# %end

# %option
# % key: limit
# % type: integer
# % description: Limit number of scenes
# % guisection: Filter
# %end

# %option G_OPT_F_INPUT
# % key: config
# % label: Full path to yaml config file
# % required: no
# % guisection: Config
# %end

# %option
# % key: area_relation
# % type: string
# % description: Spatial relation of footprint to AOI
# % options: Intersects,Contains,IsWithin
# % required: no
# % guisection: Region
# %end

# %option G_OPT_V_OUTPUT
# % key: footprints
# % description: Name for output vector map with footprints
# % required: no
# % guisection: Output
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
# % required: no
# % guisection: Filter
# %end

# %option G_OPT_F_INPUT
# % key: file
# % type: string
# % multiple: no
# % label: File with a list of scenes to read
# % description: Can be either a text file (one product ID per line), or a geojson file that was created by i.eodag
# % required: no
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
# % required: no
# % guisection: Sort
# %end

# %option
# % key: order
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: asc
# % required: no
# % guisection: Sort
# %end

# %option
# % key: query
# % multiple: yes
# % label: Extra searching parameters to use in the search
# % description: Note: Make sure to use provided options when possible, otherwise the values might not be recognized
# % required: no
# % guisection: Filter
# %end

# %option
# % key: start
# % type: string
# % label: Start date (ISO 8601 Format)
# % description: By default it is 60 days ago
# % required: no
# % guisection: Filter
# %end

# %option
# % key: end
# % type: string
# % label: End date (ISO 8601 Format)
# % description: By default it is the current date and time
# % required: no
# % guisection: Filter
# %end

# %option G_OPT_F_OUTPUT
# % key: save
# % type: string
# % description: Geojson file name to save the search results in
# % required: no
# % guisection: Output
# %end

# %option
# % key: print
# % type: string
# % description: Print the available options of the given value in JSON
# % options: products,providers,queryables,config
# % required: no
# % guisection: Print
# %end

# %rules
# % exclusive: file, id
# % exclusive: -l, -j
# % requires: -l, producttype, file, id
# % requires: -j, producttype, file, id
# % exclusive: -l, print
# % exclusive: -j, print
# % exclusive: minimum_overlap, area_relation
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
from collections import OrderedDict

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
            "lonmin": float(info["nw_long"]),
            "latmin": float(info["sw_lat"]),
            "lonmax": float(info["ne_long"]),
            "latmax": float(info["nw_lat"]),
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
    output = kwargs.get("output")
    config = kwargs.get("config")

    # Setting the envirionmnets variables has to come before the eodag initialization
    if config:
        config_file = Path(options["config"])
        if not config_file.is_file():
            gs.fatal(_("Config file '{}' not found.".format(options["config"])))
        env["EODAG_CFG_FILE"] = options["config"]


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
    columns = ["id", "startTimeFromAscendingNode", "cloudCover", "productType"]
    columns_NA = ["id_NA", "time_NA", "cloudCover_NA", "productType_NA"]
    for product in products:
        product_line = ""
        for i, column in enumerate(columns):
            if column in product.properties:
                product_attribute_value = product.properties[column]
            else:
                product_attribute_value = None
            # Display NA if not available
            if product_attribute_value is None:
                product_attribute_value = columns_NA[i]
            else:
                if column == "cloudCover":
                    # Special formatting for cloud cover
                    product_attribute_value = f"{product_attribute_value:2.0f}%"
                elif column == "startTimeFromAscendingNode":
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
                if "startTimeFromAscendingNode" not in first.properties:
                    continue
                first_value = first.properties["startTimeFromAscendingNode"]
                second_value = second.properties["startTimeFromAscendingNode"]
            elif sort_key == "cloudcover":
                if "cloudCover" not in first.properties:
                    continue
                first_value = first.properties["cloudCover"]
                second_value = second.properties["cloudCover"]
            if first_value < second_value:
                return 1 if sort_order == "desc" else -1
            elif first_value > second_value:
                return -1 if sort_order == "desc" else 1
        return 0

    search_result.sort(key=cmp_to_key(products_compare))
    return search_result


def save_footprints(search_result, map_name):
    """Save products footprints as a vector map in the current mapset.

    Reprojection is done on the fly.

    :param search_results: EO products whose footprints are to be saved.
    :type search_result: class'eodag.api.search_result.SearchResult'

    :param map_name: Footprint name to be used.
    :type map_name: str
    """
    gs.message(_("Writing footprints into <{}>...").format(map_name))

    geojson_temp_dir = gs.tempdir()
    geojson_temp_file = os.path.join(geojson_temp_dir, "search_result.geojson")
    save_search_result(search_result, geojson_temp_file)

    # coordinates of footprints are in WKT -> fp precision issues
    # -> snap
    gs.run_command(
        "v.import",
        input=geojson_temp_file,
        output=map_name,
        snap=1e-10,
        quiet=True,
    )


def save_search_result(search_result, file_name):
    """Save search results to files.

    The search result is saved using EODAG serialize method,
    saving it in a format that can be read again by i.eodag
    to restore the search results.

    :param search_result: Search result with EO products to be saved.
    :type search_result: class'eodag.api.search_result.SearchResult'

    :param file_name: File to save search result in.
    :type file_name: str
    """
    if file_name[-8:].lower() != ".geojson":
        file_name += ".geojson"
        gs.warning(
            _(
                "Search results are saved in geojson format, which doesn't match the file extension. Search result will be saved in '{}'".format(
                    file_name
                )
            )
        )
    gs.verbose(_("Saving searchin result in '{}'".format(file_name)))
    dag.serialize(search_result, filename=file_name)


def print_eodag_configuration(**kwargs):
    """Print EODAG currently recognized configurations in JSON format.

    :param provider: Print the configuration for only the given provider.
    :type provider: dict
    """
    provider = kwargs["provider"]

    def to_dict(config):
        ret_dict = dict()
        if isinstance(config, dict):
            # If the current config is a dict of providers configs
            for key, val in config.items():
                ret_dict[key] = to_dict(val)
        else:
            # Parsing a provider's configuration
            for key, val in config.__dict__.items():
                if isinstance(val, eodag.config.PluginConfig):
                    ret_dict[key] = to_dict(val)
                else:
                    ret_dict[key] = val
        return ret_dict

    if provider:
        print(json.dumps(to_dict(dag.providers_config[provider]), indent=4))
    else:
        print(json.dumps(to_dict(dag.providers_config), indent=4))


def print_eodag_providers(**kwargs):
    """Print providers available in JSON format.

    :param kwargs: Restricts providers to providers offering specified product type.
    :type kwargs: dict
    """
    product_type = kwargs["producttype"]
    if product_type:
        gs.message(_("Recongnized providers offering {}".format(product_type)))
    else:
        gs.message(_("Recongnizaed providers"))
    print(
        json.dumps(
            {"providers": dag.available_providers(product_type or None)}, indent=4
        )
    )


def print_eodag_products(**kwargs):
    """Print products available in JSON format.

    :param kwargs: Restricts products to products offered by specific provider
                   or specifies product type.
    :type kwargs: dict
    """
    provider = kwargs["provider"]
    product_type = kwargs["producttype"]
    if provider:
        gs.message(_("Recognized products offered by {}".format(provider)))
    else:
        gs.message(_("Recongnizaed providers"))
    products = dag.list_product_types(provider or None)
    if product_type:
        for product in products:
            if product["ID"] == product_type:
                products = [product]
    print(json.dumps({"products": products}, indent=4))


def print_eodag_queryables(**kwargs):
    """Print queryables info for given provider and/or product type in JSON format.

    :param kwargs: options/flags from gs.parser, with the crietria that will
                   be used for filtering.
    :type kwargs: dict
    """
    provider = kwargs["provider"]
    product_type = kwargs["producttype"]
    gs.message(_("Available queryables"))
    queryables = dag.list_queryables(
        provider=provider or None, productType=product_type or None
    )

    # Literal is for queryables that have a certain list of options to choose from.
    # Annotated is for queryables that accept a certain range e.g. cloudCover has range [0, 100].
    # TODO: It is assumed that if the type is Annotated, then the nested type will be int
    #       but that might not be the case.
    types_options = [
        "str",
        "int",
        "float",
        "dict",
        "list",
        "NoneType",
        "Literal",
        "Annotated",
    ]  # For testing and catching edge cases

    def get_type(info):
        potential_type = info.__args__[0]
        if potential_type.__name__ != "Optional":
            assert potential_type.__name__ in types_options
            return potential_type.__name__
        potential_type = potential_type.__args__[0]
        assert potential_type.__name__ in types_options
        return potential_type.__name__

    def is_required(info):
        return info.__metadata__[0].is_required()

    def get_default(info):
        default = info.__metadata__[0].get_default()
        return default if isinstance(default, str) else "None"

    def get_options(info):
        potential_type = info.__args__[0]
        potential_type = potential_type.__args__
        return potential_type

    def get_range(info):
        return (
            info.__args__[0].__args__[0].__metadata__[0].gt,
            info.__args__[0].__args__[0].__metadata__[1].lt,
        )

    queryables_dict = dict()
    for queryable, info in queryables.items():
        queryable_dict = dict()
        queryable_dict["required"] = is_required(info)
        queryable_dict["type"] = get_type(info)
        queryable_dict["default"] = get_default(info)
        if queryable_dict["type"] == "Literal":
            # There is a presit options by the provider
            queryable_dict["options"] = get_options(info)
        if queryable_dict["type"] == "Annotated":
            # There is a range for the queryable
            queryable_dict["type"] = "int"
            queryable_dict["range"] = get_range(info)
        if queryable_dict["type"] == "NoneType":
            queryable_dict["type"] = "str"
        queryables_dict[queryable] = queryable_dict

    print(json.dumps(queryables_dict, indent=4))


def main():
    # Products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    global dag
    setup_environment_variables(os.environ, **options, **flags)
    dag = EODataAccessGateway()
    if options["provider"]:
        dag.set_preferred_provider(options["provider"])

    dates_to_iso_format()

    if options["print"]:
        print_functions = {
            "providers": print_eodag_providers,
            "products": print_eodag_products,
            "config": print_eodag_configuration,
            "queryables": print_eodag_queryables,
        }
        print_functions[options["print"]](**options)
        return

    # Download by IDs
    # Searching for additional products will not take place
    ids_set = set()
    if options["id"]:  # Parse IDs
        ids_set = set(pid.strip() for pid in options["id"].split(","))
    elif options["file"]:
        if Path(options["file"]).is_file():
            gs.verbose(_('Reading file "{}"'.format(options["file"])))
        else:
            gs.fatal(_('Could not open file "{}"'.format(options["file"])))
        # Read IDs from TEXT file
        if options["file"][-4:] == ".txt":
            ids_set = set(
                Path(options["file"]).read_text(encoding="UTF8").strip().split("\n")
            )
        elif options["file"][-8:] == ".geojson":
            try:
                search_result = dag.deserialize_and_register(options["file"])
            except Exception as e:
                gs.error(_(e))
                gs.fatal(
                    _(
                        "File '{}' could not be read, file content is probably altered."
                    ).format(options["file"])
                )
        else:
            # Other unsupported file formats
            gs.fatal(_("Could not read file '{}'".format(options["file"])))

    if len(ids_set):
        # Remove empty string
        ids_set.discard(str())
        gs.message(_("Found {} distinct ID(s).".format(len(ids_set))))
        gs.message("\n".join(ids_set))

        # Search for products found from options["file"] or options["id"]
        search_result = search_by_ids(ids_set)
    elif "search_result" not in locals():
        items_per_page = 40
        # TODO: Check that the product exists,
        # could be handled by catching exceptions when searching...
        product_type = options["producttype"]

        # HARDCODED VALUES FOR TESTING { "lonmin": 1.9, "latmin": 43.9, "lonmax": 2, "latmax": 45, }
        geometry = get_aoi(options["map"])
        gs.verbose(_("AOI: {}".format(geometry)))

        search_parameters = {
            "items_per_page": items_per_page,
            "productType": product_type,
            "geom": geometry,
        }
        if options["query"]:
            for parameter in options["query"].split(","):
                key, value = parameter.split("=")
                search_parameters[key] = value

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
    if options["limit"]:
        search_result = SearchResult(search_result[: int(options["limit"])])

    gs.message(_("{} scenes(s) found.").format(len(search_result)))
    # TODO: Add a way to search in multiple providers at once
    #       Check for when this feature is added https://github.com/CS-SI/eodag/issues/163

    if options["save"]:
        save_search_result(search_result, options["save"])

    if options["footprints"]:
        save_footprints(search_result, options["footprints"])

    if flags["l"]:
        list_products(search_result)
    elif flags["j"]:
        list_products_json(search_result)
    else:
        # TODO: Consider adding a quicklook flag
        # TODO: Add timeout and wait parameters for downloading offline products...
        # https://eodag.readthedocs.io/en/stable/getting_started_guide/product_storage_status.html
        try:
            override_config = {}
            if options["output"]:
                override_config["outputs_prefix"] = options["output"]
            dag.download_all(search_result, **override_config)
        except MisconfiguredError as e:
            gs.fatal(_(e))


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
        from eodag.utils.exceptions import *
        import eodag
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
