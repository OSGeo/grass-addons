#!/usr/bin/env python3

############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Downloads imagery scenes e.g. Landsat, Sentinel, and MODIS
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

# %flag
# % key: b
# % description: Use the borders of the AOI polygon and not the region of the AOI
# % guisection: Filter
# %end

# %flag
# % key: s
# % description: Skip scenes that have already been downloaded
# % guisection: Filter
# %end

# %flag
# % key: p
# % description: Print compiled query string and exit
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
# % answer: 50
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

# %option
# % key: pattern
# % type: string
# % description: Filter products by id using a regular expression, e.g. 'LC09.*T1'
# % required: no
# % guisection: Filter
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
# % type: string
# % description: Field to sort values by
# % options: ingestiondate,cloudcover,footprint
# % answer: cloudcover,ingestiondate,footprint
# % required: no
# % multiple: yes
# % guisection: Sort
# %end

# %option
# % key: order
# % type: string
# % description: Sort order (see sort parameter)
# % options: asc,desc
# % answer: asc
# % required: no
# % guisection: Sort
# %end

# %option
# % key: query
# % multiple: yes
# % label: Query using extra filtering parameters
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

# %option
# % key: timeout
# % type: integer
# % description: If download fails, maximum time in minutes before stop retrying to download
# % answer: 300
# % guisection: Config
# %end

# %option
# % key: wait
# % type: integer
# % description: Wait time in minutes before retrying to download data
# % answer: 2
# % guisection: Config
# %end

# %rules
# % exclusive: file, id
# % exclusive: -l, -j
# % requires: -l, producttype, file, id
# % requires: -j, producttype, file, id
# % requires: -b, map
# % exclusive: -l, print
# % exclusive: -j, print
# % exclusive: minimum_overlap, area_relation
# %end

from __future__ import annotations

import json
import operator as op_stdlib
import os
import re
import sys
import typing
from datetime import datetime, timedelta, timezone
from hashlib import md5
from pathlib import Path
from subprocess import PIPE

import grass.script as gs
from grass.pygrass.modules import Module

try:
    import eodag

    EODAG_VERSION = int(eodag.__version__.split(".")[0])
except ImportError:
    EODAG_VERSION = None


def _parse_queryable_v4(info):
    """Parses EODAG v4 Parameter objects."""
    q_dict = {
        "required": getattr(info, "required", False),
        "default": str(getattr(info, "default", "None")),
    }
    raw_type = getattr(info, "type", str)
    q_dict["type"] = getattr(raw_type, "__name__", str(raw_type))
    if hasattr(info, "choices") and info.choices:
        q_dict["options"] = info.choices
        q_dict["type"] = "Literal"
    return q_dict


def _parse_queryable_v3(info):
    """Parses EODAG v3 TypeHint objects."""
    if not hasattr(info, "__metadata__") or not hasattr(info, "__args__"):
        return None
    try:
        meta = info.__metadata__[0]
        potential_type = info.__args__[0]

        if typing.get_origin(potential_type) is typing.Union:
            args = [a for a in typing.get_args(potential_type) if a is not type(None)]
            if args:
                potential_type = args[0]

        q_dict = {
            "required": meta.is_required(),
            "default": str(meta.get_default()),
            "type": getattr(potential_type, "__name__", str(potential_type)),
        }
        if q_dict["type"] == "Literal":
            q_dict["options"] = getattr(potential_type, "__args__", [])
        return q_dict
    except (AttributeError, IndexError, TypeError):
        return None


# --- EODAG Version Compatibility Mapping ---
# This dictionary centralizes all version-specific differences between v3 and v4.
# It allows the rest of the code to remain "version-agnostic".
EODAG_MAP = {
    3: {
        "version": 3,
        "product_type_attr": "product_type",
        "product_type_key": "productType",
        "cloud_cover_key": "cloudCover",
        "datetime_key": "startTimeFromAscendingNode",
        "providers_attr": "providers_config",
        "methods": {
            "list_collections": "list_product_types",
            "available_providers": "available_providers",
        },
        "get_providers": lambda dag, ptype: dag.available_providers(ptype),
        "getattr": lambda prod, key, m_key: prod.properties.get(
            m_key[0] if isinstance(m_key, tuple) else m_key
        ),
        "prop_map": {
            "id": "id",
            "datetime": "startTimeFromAscendingNode",
            "cloud_cover": "cloudCover",
            "collection": "productType",
            "relative_orbit": "relativeOrbitNumber",
            "instrument_mode": "instrumentMode",
            "title": "title",
            "geometry": "geometry",
        },
        "queryable_map": {},
        "format_providers": lambda p: p,
        "parse_queryable": _parse_queryable_v3,
    },
    4: {
        "version": 4,
        "product_type_attr": "collection",
        "product_type_key": "collection",
        "cloud_cover_key": "eo:cloud_cover",
        "datetime_key": "datetime",
        "providers_attr": "providers",
        "methods": {
            "list_collections": "list_collections",
            "available_providers": "providers",  # Attribute in v4
        },
        "get_providers": lambda dag, ptype: dag.providers,
        "getattr": lambda prod, key, m_key: (
            getattr(prod, key)
            if key in ("collection", "geometry")
            else next(
                (
                    prod.properties.get(k)
                    for k in (m_key if isinstance(m_key, tuple) else [m_key])
                    if prod.properties.get(k) is not None
                ),
                None,
            )
        ),
        "prop_map": {
            "id": "id",
            "datetime": "datetime",
            "cloud_cover": "eo:cloud_cover",
            "collection": "collection",
            "relative_orbit": "sat:relative_orbit",
            "instrument_mode": "instrumentMode",
            "title": "title",
            "geometry": "geometry",
        },
        "queryable_map": {
            "relativeOrbitNumber": "sat:relative_orbit",
            "sensorMode": "instrumentMode",
            "cloudCover": "eo:cloud_cover",
            "productType": "collection",
        },
        "format_providers": lambda p: list(p),
        "parse_queryable": _parse_queryable_v4,
    },
}

# Select the appropriate mapping based on detected version (defaults to v3)
VER = EODAG_MAP.get(EODAG_VERSION, EODAG_MAP[3])

# --- Compatibility Helpers ---


def get_eodag_providers(dag):
    """Retrieve the providers configuration based on version mapping."""
    return getattr(dag, VER["providers_attr"])


def get_eodag_collections(dag, provider=None):
    """List available collections/product types using the mapped method name."""
    method_name = VER["methods"]["list_collections"]
    method = getattr(dag, method_name)
    return method(provider=provider)


def get_available_providers(dag, product_type=None):
    """Get list of providers using the mapped fetcher logic."""
    fetcher = VER["get_providers"]
    return fetcher(dag, product_type)


def get_product_property(product, key):
    """Retrieve product property using version-specific mapping logic."""
    mapped_key = VER["prop_map"].get(key, key)
    return VER["getattr"](product, key, mapped_key)


def get_aoi_box(vector: str | None = None) -> str:
    """Get bounding box of the vector map or computational region.

    Fetches the bounding box of the vector map or the current
    computational region and returns it as a WKT Polygon it
    with coordinates in CRS84.

    :param vector: Vector map
    :type vector: str

    :return: Bounding box represented as a WKT Polygon.
    :rtype: str
    """
    polygon_template = (
        "POLYGON(({nw_lon} {nw_lat}, {ne_lon} {ne_lat},"
        " {se_lon} {se_lat}, {sw_lon} {sw_lat}, {nw_lon} {nw_lat}))"
    )
    args = {}
    if vector:
        args["vector"] = vector

    # are we in LatLong location?
    kv = gs.parse_command("g.proj", flags="j")
    if "+proj" not in kv:
        gs.fatal(
            _("Unable to get AOI bounding box: unprojected location not supported"),
        )
    if kv["+proj"] != "longlat":
        info = gs.parse_command("g.region", flags="uplg", **args)
        return polygon_template.format(
            nw_lat=info["nw_lat"],
            nw_lon=info["nw_long"],
            ne_lat=info["ne_lat"],
            ne_lon=info["ne_long"],
            sw_lat=info["sw_lat"],
            sw_lon=info["sw_long"],
            se_lat=info["se_lat"],
            se_lon=info["se_long"],
        )
    info = gs.parse_command("g.region", flags="upg", **args)
    return polygon_template.format(
        nw_lat=info["n"],
        nw_lon=info["w"],
        ne_lat=info["n"],
        ne_lon=info["e"],
        sw_lat=info["s"],
        sw_lon=info["w"],
        se_lat=info["s"],
        se_lon=info["e"],
    )


def get_aoi(vector: str | None = None) -> str:
    """Parse and return the AOI.

    :param vector: Vector map
    :type vector: str

    :return: Area of Interest represented as a WKT Polygon.
    :rtype: str
    """
    # If the 'b' flag is set then we use the Polygon borders
    # If not set then we use the bounding box
    # If no vector map is set then we use the bounding box
    # of the current compuational region
    if not vector or not flags["b"]:
        return get_aoi_box(vector)

    proj = gs.parse_command("g.proj", flags="j")
    if "+proj" not in proj:
        gs.fatal(_("Unable to get AOI: unprojected location not supported"))

    if not gs.find_file(vector, element="vector")["file"]:
        gs.fatal(
            _("Unable to get AOI: vector map <{}> could not be found").format(vector),
        )

    args = {}
    args["input"] = vector

    if gs.vector_info_topo(vector)["areas"] <= 0:
        gs.fatal(_("No areas found in AOI map <{}>...").format(vector))
    elif gs.vector_info_topo(vector)["areas"] > 1:
        gs.warning(
            _(
                "More than one area found in AOI map <{}>. \
                      Using only the first area...",
            ).format(vector),
        )

    geom_dict = gs.parse_command("v.out.ascii", format="wkt", **args)
    num_vertices = len(str(geom_dict.keys()).split(","))
    geom = next(iter(geom_dict))
    if proj["+proj"] != "longlat":
        gs.verbose(
            _("Generating WKT from AOI map ({} vertices)...").format(num_vertices),
        )
        # NOTE: Might need to check for number of coordinates
        #       Make sure it won't cause problems like in:
        #       https://github.com/OSGeo/grass-addons/blob/8eb244b8f229d668ed5306ed9f18f3b0b08c1e45/src/imagery/i.sentinel/i.sentinel.download/i.sentinel.download.py#L273
        # As for now, EODAG takes care of the Polygon simplification if needed
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
            ],
        ) + "))"
        return projected_geom
    return geom


def search_by_ids(ids_set: set, module_options: dict, eodag_api=None):
    """Search for products based on their ids.

    :param ids_set: Set of unique products' ids.
    :type ids_set: list
    :param module_options: Dict with GRASS module options.
    :type module_options: dict

    :return: EO products found by searching with 'search_parameters'
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    # Remove empty string
    ids_set.discard("")
    # Search for products found from options["file"] or options["id"]
    gs.verbose(_("Searching for {} distinct ID(s).").format(len(ids_set)))
    search_result = []
    for query_id in ids_set:
        gs.info(_("Searching for {}").format(query_id))
        if not module_options["producttype"]:
            gs.warning(_("The producttype option is not set"))

        search_params = {
            "id": query_id,
            "provider": module_options.get("provider") or None,
            "count": True,
        }
        product_type = module_options.get("producttype") or None
        search_params[VER["product_type_key"]] = product_type

        product = eodag_api.search(**search_params)
        if product.number_matched > 1:
            gs.warning(
                _("{}\nCould not be uniquely identified. Skipping...").format(query_id),
            )
        elif product.number_matched == 0 or not product[0].properties["id"].startswith(
            query_id,
        ):
            gs.warning(_("{} not found. Skipping...").format(query_id))
        else:
            search_result.append(product[0])
    gs.verbose(_("Found {} scene(s).").format(len(search_result)))
    return SearchResult(search_result)


def setup_environment_variables(env: dict, **kwargs) -> None:
    """Set the eodag environment variables based on the provided options/flags.

    :param env: Environment variables dictionary to be updated.
    :type env: dict
    :param kwargs: options/flags from gs.parser
    :type kwargs: dict
    """
    config = kwargs.get("config")

    # Setting the environment variables has to come before the eodag initialization
    if config:
        config_file = Path(config)
        if not config_file.is_file():
            gs.fatal(_("Config file '{}' not found.").format(config))
        env["EODAG_CFG_FILE"] = config


def normalize_time(datetime_str: str) -> str:
    """Unify the different ISO formats into 'YYYY-MM-DDTHH:MM:SS'.

    :param datetime_str: Datetime in ISO format
    :type datetime_str: str

    :return: Datetime converted to 'YYYY-MM-DDTHH:MM:SS'
    :rtype: str
    """
    # Remove microseconds
    if datetime_str.find("Z") != -1:
        datetime_str = datetime_str[: datetime_str.find("Z")]
    normalized_datetime = datetime.fromisoformat(datetime_str)
    if normalized_datetime.tzinfo is None:
        return normalized_datetime.strftime("%Y-%m-%dT%H:%M:%S")
    return normalized_datetime.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")


def list_products(products) -> None:
    """List products on the Standard Output stream (shell).

    :param products: EO poducts to be listed
    :type products: class:'eodag.api.search_result.SearchResult'
    """
    # Map internal column names to the keys used by get_product_property
    display_keys = {
        "id": "id",
        "startTimeFromAscendingNode": VER["datetime_key"],
        "cloudCover": VER["cloud_cover_key"],
        "productType": VER["product_type_key"],
    }

    columns = ["id", "startTimeFromAscendingNode", "cloudCover", "productType"]
    columns_na = ["id_NA", "time_NA", "cloudCover_NA", "productType_NA"]
    for product in products:
        product_line = ""
        for i, column in enumerate(columns):
            # Get the actual key/attribute name for the current EODAG version
            actual_key = display_keys.get(column)
            product_attribute_value = get_product_property(product, actual_key)

            # Display NA if not available
            if product_attribute_value is None:
                product_attribute_value = columns_na[i]
            elif column == "cloudCover":
                # Special formatting for cloud cover
                product_attribute_value = f"{float(product_attribute_value):2.0f}%"
            elif column == "startTimeFromAscendingNode":
                # Special formatting for datetime
                try:
                    product_attribute_value = normalize_time(
                        str(product_attribute_value)
                    )
                except (ValueError, TypeError):
                    # Invalid ISO Format
                    gs.warning(
                        _("Timestamp {} is not compliant with ISO 8601").format(
                            product_attribute_value,
                        ),
                    )
                    product_attribute_value = str(
                        get_product_property(product, actual_key) or "time_NA"
                    )
            if i != 0:
                product_line += " "
            product_line += str(product_attribute_value)
        print(product_line)


def list_products_json(products) -> None:
    """List products on the Standard Output stream (shell) in JSON format.

    :param products: EO poducts to be listed
    :type products: class:'eodag.api.search_result.SearchResult'
    """
    if hasattr(products, "as_dict"):
        print(json.dumps(products.as_dict(), indent=4))
    else:
        print(json.dumps(products.as_geojson_object(), indent=4))


def remove_duplicates(search_result):
    """Remove duplicated products, in case a provider returns a product multiple times."""
    filtered_result = []
    is_added = set()
    for product in search_result:
        if product.properties["id"] in is_added:
            continue
        is_added.add(product.properties["id"])
        filtered_result.append(product)
    gs.verbose(
        _("Filtered out {} duplicate products.").format(
            len(search_result) - len(filtered_result)
        )
    )
    return SearchResult(filtered_result)


def dates_to_iso_format() -> None:
    """Convert the start/end options to the isoformat and save them in-place."""
    end_date = options["end"]
    if not options["end"]:
        end_date = datetime.now(timezone.utc).isoformat()
    try:
        end_date = normalize_time(end_date)
    except ValueError:
        gs.fatal(_("Could not parse 'end' time."))

    start_date = options["start"]
    if not options["start"]:
        delta_days = timedelta(60)
        start_date = (datetime.fromisoformat(end_date) - delta_days).isoformat()

    # Ensure start_date is a string before passing to normalize_time
    if not isinstance(start_date, str):
        start_date = str(start_date)

    try:
        start_date = normalize_time(start_date)
    except ValueError:
        gs.fatal(_("Could not parse 'start' time."))

    if end_date < start_date:
        # Standard GRASS error message
        gs.error(
            _("End Date <{}> can not come before start Date <{}>").format(
                end_date, start_date
            )
        )
        # Force non-zero exit code for the test suite
        sys.exit(1)

    options["start"] = start_date
    options["end"] = end_date


def parse_query(query: str | None = None):
    """Parse query string.

    :param query: WKT String with the geometry to filter with respect to
    :type query: str

    :returns: A dictionary of queryables as keys, and a list of tuples,
              each tuple consists of a queryable value and an operator,
              as the dictionary values.
              Dict["queryable", List(Tuple("queryable_value", "operator"))]
    :rtype: Dict[str, List(Tuple(str, str))]

    """
    valid_operators = ["eq", "ne", "ge", "gt", "le", "lt"]
    default_operator = "eq"
    query_list = []
    if query is None:
        return query_list
    for parameter in map(str.strip, query.split(",")):
        if not parameter:
            continue
        try:
            key, values = map(str.strip, parameter.split("="))
        except ValueError as e:
            gs.debug(e)
            gs.fatal(_("Queryable <{}> could not be parsed").format(parameter))
        if key == "start":
            try:
                start_date = normalize_time(values)
                query_list.append(("start", (start_date, default_operator)))
            except ValueError as e:
                gs.debug(e)
                gs.fatal(
                    _(
                        "Queryable <{}> could not be parsed\nDate must be ISO formated",
                    ).format(parameter),
                )
            continue
        if key == "end":
            try:
                end_date = normalize_time(values)
                query_list.append(("end", (end_date, default_operator)))
            except ValueError as e:
                gs.debug(e)
                gs.fatal(
                    _(
                        "Queryable <{}> could not be parsed\nDate must be ISO formated",
                    ).format(parameter),
                )
            continue
        values_operators = []
        for value in map(str.strip, values.split("|")):
            operator = None
            if not value:
                continue
            if value.find(";") != -1:
                try:
                    value, operator = map(str.strip, value.split(";"))
                except ValueError:
                    gs.fatal(
                        _("Queryable <{}> could not be parsed\n").format(parameter),
                    )
                if operator not in valid_operators:
                    gs.fatal(
                        _(
                            "Invalid operator <{0}> for queryable <{1}>. Available operators {2}",
                        ).format(operator, key, valid_operators),
                    )
            try:
                value = float(value)
            except ValueError:
                # Not a numeric value
                if value.lower() == "none" or value.lower() == "null":
                    # User is allowing for scenes with Null values
                    value = None
            values_operators.append((value, operator))
        query_list.append((key, values_operators))
    return query_list


def filter_result(search_result, geometry=None, queryables=None, **kwargs):
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
    if search_result is None:
        search_result = SearchResult(None)

    default_operator = "eq"

    prefilter_count = len(search_result)
    area_relation = kwargs["area_relation"]
    minimum_overlap = kwargs["minimum_overlap"]
    cloud_cover = kwargs["clouds"]
    start_date = kwargs["start"]
    end_date = kwargs["end"]

    # If geometry is not set, but we need the geometry
    # for filtering, then get the geometry
    if geometry is None and (area_relation is not None or minimum_overlap is not None):
        geometry = get_aoi(kwargs["map"])

    if area_relation:
        # Product's geometry intersects with AOI
        if area_relation == "Intersects":
            search_result = search_result.filter_overlap(
                geometry=geometry,
                intersects=True,
            )
        # Product's geometry contains the AOI
        elif area_relation == "Contains":
            search_result = search_result.filter_overlap(
                geometry=geometry,
                contains=True,
            )
        # Product's geometry is within the AOI
        elif area_relation == "IsWithin":
            search_result = search_result.filter_overlap(geometry=geometry, within=True)

    if minimum_overlap:
        # Percentage of the AOI area covered by the product's geometry
        search_result = search_result.filter_overlap(
            geometry=geometry,
            minimum_overlap=int(minimum_overlap),
        )

    if cloud_cover:
        search_result = search_result.filter_property(
            operator="le", **{VER["cloud_cover_key"]: int(cloud_cover)}
        )

    queryable_map = VER["queryable_map"]

    # queryables are formatted as follow:
    # [('queryable_1' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ('queryable_2' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ('queryable_3' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ...
    #  ...
    # ]
    if queryables:
        op_map = {
            "eq": op_stdlib.eq,
            "ne": op_stdlib.ne,
            "lt": op_stdlib.lt,
            "le": op_stdlib.le,
            "gt": op_stdlib.gt,
            "ge": op_stdlib.ge,
        }
        for queryable, values in queryables:
            if queryable in {"start", "end"}:
                continue

            v4_queryable = queryable_map.get(queryable, queryable)
            tmp_search_result_list = []
            for value, operator_str in values:
                if operator_str not in op_map:
                    gs.warning(
                        _(
                            "Invalid operator <{0}> for queryable <{1}>\n"
                            "Operator <{2}> will be used instead",
                        ).format(operator_str, queryable, default_operator),
                    )
                    operator_str = default_operator

                op_func = op_map[operator_str]
                filtered_data = []

                for product in search_result:
                    prop_val = get_product_property(product, v4_queryable)

                    if prop_val is None:
                        if value is None and op_func(None, None):
                            filtered_data.append(product)
                        continue

                    try:
                        if isinstance(value, (int, float)):
                            prop_val = type(value)(prop_val)
                        elif isinstance(value, str):
                            prop_val = str(prop_val)
                    except (ValueError, TypeError):
                        pass

                    try:
                        if op_func(prop_val, value):
                            filtered_data.append(product)
                    except TypeError:
                        pass

                tmp_search_result_list.extend(filtered_data)
            search_result = SearchResult(tmp_search_result_list)

    if options["pattern"]:
        pattern = re.compile(options["pattern"])
        search_result = SearchResult(
            [p for p in search_result if pattern.fullmatch(p.properties["title"])],
        )

    # Filter search results by sensing date
    if start_date or end_date:
        search_result = search_result.filter_date(start=start_date, end=end_date)

    postfilter_count = len(search_result)
    gs.verbose(
        _("{} product(s) filtered out in total.").format(
            prefilter_count - postfilter_count,
        ),
    )

    return search_result


def sort_result(search_result):
    """Sorts search results according to options['sort'] and options['order']."""
    sort_key_map = {
        "ingestiondate": VER["datetime_key"],
        "title": "title",
        "cloudcover": VER["cloud_cover_key"],
        "footprint": "geometry",
    }

    actual_sort_keys = [
        sort_key_map.get(key)
        for key in options["sort"].split(",")
        if sort_key_map.get(key)
    ]

    def safe_sort_key(product, sort_key):
        val = get_product_property(product, sort_key)
        if val is None:
            return ""
        # If the value is a geometry object, convert it to string (WKT) for sorting
        if hasattr(val, "wkt"):
            return val.wkt
        return val

    search_result.sort(
        reverse=options["order"] == "desc",
        key=lambda product: [
            (
                (get_product_property(product, sort_key) is None)
                ^ (options["order"] == "desc"),
                safe_sort_key(product, sort_key),
            )
            for sort_key in actual_sort_keys
        ],
    )
    return search_result


def skip_existing(output, search_result):
    """Remove products that are already downloaded and saved in 'output' directory.

    :param output: Output directory whose files will be compared with the scenes.
    :type output: class'eodag.api.search_result.SearchResult'

    :param search_results: EO products to be checked for existence in 'output' directory.
    :type search_result: class'eodag.api.search_result.SearchResult'

    :return: Sorted EO products
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    suffixes = {"", ".zip", ".ZIP"}

    # Check for previously downloaded scenes
    output = Path(output)

    # Check if directory doesn't exist or if it is empty

    if not output.exists() or next(os.scandir(output), None) is None:
        gs.verbose(_("Directory '{}' is empty, no scenes to skip").format(output))
        return search_result
    downloaded_dir = output / ".downloaded"
    if not downloaded_dir.exists() or next(os.scandir(downloaded_dir), None) is None:
        gs.verbose(
            _("The `.download` directory in '{}' is empty, no scenes to skip").format(
                output,
            ),
        )
        return search_result

    for scene in search_result:
        for suffix in suffixes:
            scene_file = output / (scene.properties["title"] + suffix)
            if scene_file.exists():
                creation_time = datetime.fromtimestamp(
                    os.path.getctime(scene_file), tz=timezone.utc
                ).strftime("%Y-%m-%dT%H:%M:%S")
                ingestion_time = scene.properties.get(
                    "modificationDate",
                    scene.properties.get(
                        "publicationDate",
                        scene.properties.get("creationDate"),
                    ),
                )
                if ingestion_time and normalize_time(ingestion_time) <= normalize_time(
                    creation_time,
                ):
                    # This is to check that the file was completely downloaded
                    # without interruptions.
                    # The reason this works:
                    # When eodag completely download a scene, it saves a file
                    # with the scene's remote location
                    # in `.download`. The name of that file is the MD5 hash of
                    # the scenes remote location
                    # so here we are checking for the existance of that file.
                    product_type_for_hash = getattr(scene, VER["product_type_attr"])
                    product_id_for_hash = get_product_property(scene, "id")

                    hashed_file = (
                        downloaded_dir
                        / md5(
                            (
                                product_type_for_hash + "-" + product_id_for_hash
                            ).encode(),
                        ).hexdigest()
                    )
                    if not hashed_file.exists():
                        continue
                    gs.message(
                        _("Skipping scene: {} which is already downloaded.").format(
                            scene.properties["title"],
                        ),
                    )
                    search_result.remove(scene)
                    break
    return search_result


def save_footprints(search_result, map_name, eodag_api) -> None:
    """Save product-footprints as a vector map in the current mapset.

    Reprojection is done on the fly.

    :param search_results: EO products whose footprints are to be saved.
    :type search_result: class'eodag.api.search_result.SearchResult'

    :param map_name: Footprint name to be used.
    :type map_name: str
    """
    gs.message(_("Writing footprints into <{}>...").format(map_name))

    geojson_temp_dir = gs.tempdir()
    geojson_temp_file = Path(geojson_temp_dir) / "search_result.geojson"
    save_search_result(search_result, str(geojson_temp_file), eodag_api)

    # coordinates of footprints are in WKT -> fp precision issues
    # -> snap
    gs.run_command(
        "v.import",
        input=geojson_temp_file,
        output=map_name,
        snap=1e-10,
        quiet=True,
    )


def save_search_result(search_result, file_name, eodag_api) -> None:
    """Save search results to file.

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
                "Search results are saved in geojson format, "
                "which doesn't match the file extension. "
                "Search result will be saved in '{}'",
            ).format(file_name),
        )
    gs.verbose(_("Saving search result in '{}'").format(file_name))
    eodag_api.serialize(search_result, filename=file_name)


def print_eodag_configuration(eodag_api, **kwargs) -> None:
    """Print EODAG currently recognized configurations in JSON format.

    :param provider: Print the configuration for only the given provider.
    :type provider: str
    """
    provider = kwargs.get("provider")

    # Use the wrapper to get the correct providers source (v3 vs v4)
    providers_source = get_eodag_providers(eodag_api)

    def to_dict(obj):
        """Recursive helper to convert EODAG objects to serializable dicts."""
        if isinstance(obj, dict):
            return {k: to_dict(v) for k, v in obj.items()}
        elif hasattr(obj, "__dict__"):
            # This handles PluginConfig and other EODAG internal objects
            ret_dict = {}
            for key, val in vars(obj).items():
                # Skip internal/private attributes to keep JSON clean
                if not key.startswith("_"):
                    ret_dict[key] = to_dict(val)
            return ret_dict
        elif isinstance(obj, (list, tuple)):
            return [to_dict(item) for item in obj]
        return obj

    if provider:
        # Check if the requested provider actually exists
        if provider in providers_source:
            conf = to_dict(providers_source[provider])
            print(json.dumps(conf, indent=4))
        else:
            gs.fatal(_("Provider '{}' not found in configuration.").format(provider))
    else:
        # Print configuration for all providers
        print(json.dumps(to_dict(providers_source), indent=4))


def print_eodag_providers(eodag_api, **kwargs) -> None:
    """Print providers available in JSON format."""
    product_type = kwargs["producttype"]
    if product_type:
        gs.message(_("Recognized providers offering {}").format(product_type))
    else:
        gs.message(_("Recognized providers"))

    providers = get_available_providers(eodag_api, product_type)

    providers = VER["format_providers"](providers)

    print(json.dumps({"providers": providers}, indent=4))


def print_eodag_products(eodag_api, **kwargs) -> None:
    """Print products available in JSON format."""
    provider = kwargs.get("provider")
    product_type = kwargs.get("producttype")

    if provider:
        gs.message(_("Recognized product types offered by {}").format(provider))
    else:
        gs.message(_("Recognized product types"))

    raw_products = get_eodag_collections(eodag_api, provider)

    products_to_print = []
    for p in raw_products:
        # v4 Collection objects have a .id attribute. v3 dicts have "ID" key.
        if isinstance(p, dict):
            p_id = p.get("ID")  # This is fine for v3
        else:
            p_id = getattr(p, "id", str(p))

        products_to_print.append({"ID": p_id})

    if product_type:
        pattern = re.compile(re.escape(product_type), re.IGNORECASE)
        products_to_print = [p for p in products_to_print if pattern.search(p["ID"])]

    print(json.dumps({"products": products_to_print}, indent=4))


def print_eodag_queryables(eodag_api, **kwargs) -> None:
    """Print queryables info for given provider and/or product type in JSON format.

    The function extracts metadata (type, default value, and requirement)
    from EODAG parameters and outputs them as a GRASS-friendly JSON.
    """
    provider = kwargs.get("provider")
    product_type = kwargs.get("producttype")
    gs.message(_("Available queryables"))

    # list_queryables returns a dict of parameters
    list_queryables_params = {
        "provider": provider or None,
    }
    list_queryables_params[VER["product_type_key"]] = product_type or None

    queryables = eodag_api.list_queryables(**list_queryables_params)

    # Filter for types that can be easily represented as strings in GRASS CLI
    supported_types = ["str", "int", "float", "Literal", "bool"]
    queryables_dict = {}

    for queryable, info in queryables.items():
        # 'geom' is handled separately by GRASS AOI logic
        if queryable == "geom":
            continue

        parser = VER["parse_queryable"]
        q_dict = parser(info)

        # Final check: only include queryables with supported types
        if q_dict and q_dict.get("type") in supported_types:
            queryables_dict[queryable] = q_dict

    # Filter out NoneType which is often interpreted as str
    queryables_dict.pop("NoneType", None)

    print(json.dumps(queryables_dict, indent=4))


def print_query(geometry, queryables, **kwargs) -> None:
    """Print the query parameters that will be used to search for products."""
    query_dict = {
        "flags": "".join([f for f in flags if flags[f] and f != "p"]),
        "AOI": geometry,
        "provider": kwargs.get("provider") or "ANY",
        "producttype": kwargs.get("producttype") or "ANY",
        "area_relation": kwargs.get("area_relation") or "ANY",
        "minimum_overlap": kwargs.get("minimum_overlap") or "ANY",
        "pattern": kwargs.get("pattern") or "ANY",
        "start (ge)": kwargs.get("start") or "ANY",
        "end (le)": kwargs.get("end") or "ANY",
        "limit": kwargs.get("limit") or "ANY",
    }
    if kwargs["clouds"]:
        query_dict["cloudCover (le)"] = kwargs["clouds"]
    default_operator = "eq"
    query_dict["queryables"] = {}
    for k, v in queryables:
        for value in v:
            operator = value[1] or default_operator
            query_dict["queryables"][f"{k} ({operator})"] = value[0]
    print(json.dumps(query_dict, indent=4))


def main() -> None:
    """Main execution logic for the i.eodag GRASS module."""
    # Setup environment variables for EODAG configuration
    setup_environment_variables(os.environ, **options, **flags)
    dag = EODataAccessGateway()

    # Provider validation
    provider = None
    if options["provider"]:
        available_providers = get_available_providers(dag)
        if options["provider"] not in available_providers:
            gs.fatal(_("Provider {} not available.").format(options["provider"]))
        dag.set_preferred_provider(options["provider"])
        provider = options["provider"]

    # AOI (Area of Interest) retrieval
    geometry = get_aoi(options["map"])
    gs.verbose(_("AOI: {}").format(geometry))

    # Product type validation (Attribute-safe for v3/v4)
    if options["producttype"]:
        collections = get_eodag_collections(dag, provider)
        # Extract IDs: v3 uses dict keys, v4 uses .id attribute
        available_types = {
            p["ID"] if isinstance(p, dict) else getattr(p, "id", str(p))
            for p in collections
        }

        # Only validate if EODAG returned any collections (handles cases without API keys)
        if available_types and options["producttype"] not in available_types:
            gs.fatal(
                _("Product type <{}> not available.").format(options["producttype"])
            )
        elif not available_types:
            gs.warning(_("No collections found. Skipping product type validation."))

    # Parse query parameters
    queryables = parse_query(options["query"])
    for queryable, values in queryables:
        if queryable == "start":
            if options["start"]:
                gs.fatal(_("Queryable <start> can not be set twice"))
            options["start"] = values[0][0]
        if queryable == "end":
            if options["end"]:
                gs.fatal(_("Queryable <end> can not be set twice"))
            options["end"] = values[0][0]

    # Handle metadata print requests (if requested, exit early)
    if options["print"]:
        print_functions = {
            "providers": print_eodag_providers,
            "products": print_eodag_products,
            "config": print_eodag_configuration,
            "queryables": print_eodag_queryables,
        }
        print_functions[options["print"]](dag, **options)
        return

    # Handle query preview flag
    if flags["p"]:
        print_query(geometry, queryables, **options)
        return

    # Initialize search_result to avoid UnboundLocalError
    search_result = SearchResult([])

    # Execute Search Logic
    id_file = Path(options["file"]) if options["file"] else None
    if id_file and not id_file.is_file():
        gs.fatal(_('Could not open file "{}"').format(options["file"]))

    if options["id"]:
        # Search by comma-separated IDs
        search_result = search_by_ids(
            {
                pid.strip() for pid in options["id"].split(",")
            },  # product.id is consistent
            options,
            eodag_api=dag,
        )
    elif id_file and id_file.suffix.lower() == ".geojson":
        # Restore search results from GeoJSON
        gs.verbose(
            _("Reading stored search result from file <{}>").format(options["file"])
        )
        try:
            search_result = dag.deserialize_and_register(options["file"])
        except RuntimeError:
            gs.fatal(_("File '{}' could not be read by EODAG.").format(options["file"]))

    elif id_file and id_file.suffix.lower() == ".txt":
        # Read IDs from text file
        try:
            ids = {
                pid.strip()
                for pid in id_file.read_text(encoding="UTF8").strip().split("\n")
            }
            search_result = search_by_ids(ids, options, eodag_api=dag)
        except (OSError, UnicodeDecodeError):
            gs.fatal(
                _("Unable to read product IDs from file <{}>.").format(options["file"])
            )

    elif id_file:
        gs.fatal(_("File type '{}' is not supported.").format(id_file.suffix.lower()))

    else:
        # Standard parameter-based search
        dates_to_iso_format()  # Validates date order and formats

        product_type = options["producttype"]
        search_parameters = {
            "geom": geometry,
            "provider": provider,
        }

        search_parameters[VER["product_type_key"]] = product_type

        if options["clouds"]:
            search_parameters[VER["cloud_cover_key"]] = options["clouds"]

        search_parameters["start"] = options["start"]
        search_parameters["end"] = options["end"]

        if not options["area_relation"]:
            options["area_relation"] = "Intersects"

        # Conduct the actual search
        search_result = dag.search_all(**search_parameters)
        gs.verbose(_("Filtering results..."))
        search_result = filter_result(search_result, geometry, queryables, **options)

    # Post-processing of results
    search_result = remove_duplicates(search_result)

    if flags["s"]:
        search_result = skip_existing(options["output"], search_result)

    gs.verbose(_("Sorting results..."))
    search_result = sort_result(search_result)

    # Apply limits
    if options["limit"] and not (options["id"] or options["file"]):
        search_result = SearchResult(search_result[: int(options["limit"])])

    # Outputs: Footprints and GeoJSON
    if options["footprints"]:
        save_footprints(search_result, options["footprints"], dag)

    gs.verbose(_("{} scene(s) found.").format(len(search_result)))

    if options["save"]:
        save_search_result(search_result, options["save"], dag)

    # Display or Download
    if flags["l"]:
        list_products(search_result)
    elif flags["j"]:
        list_products_json(search_result)
    else:
        # TODO: Consider adding a quicklook flag
        # --- Download Logic with Automatic OTP ---
        try:
            # TODO: Would be better if we could find a way to not ask the user for the OTP manually
            providers = {scene.provider for scene in search_result}
            if "creodias" in providers:
                gs.message(
                    _(
                        "Please enter Creodias OTP, to discard Creodias scenes enter '-': ",
                    ),
                )
                creodias_otp = input().strip()

                if creodias_otp == "-":
                    search_result = SearchResult(
                        [
                            scene
                            for scene in search_result
                            if scene.provider != "creodias"
                        ],
                    )
                else:
                    providers_cfg = get_eodag_providers(dag)
                    if "creodias" in providers_cfg:
                        providers_cfg["creodias"].auth.credentials["totp"] = (
                            creodias_otp
                        )
                        if hasattr(dag, "_plugins_manager"):
                            dag._plugins_manager.get_auth_plugin(
                                "creodias"
                            ).authenticate()
                    else:
                        gs.warning(
                            _(
                                "Creodias configuration not found, skipping OTP assignment."
                            )
                        )

            custom_config = {
                "timeout": int(options["timeout"]),
                "wait": int(options["wait"]),
            }
            if not search_result:
                gs.message(_("Nothing to download.\nExiting..."))
                return
            if options["output"]:
                custom_config["output_dir"] = options["output"]

            dag.download_all(search_result, **custom_config)

        except MisconfiguredError as e:
            gs.fatal(_("EODAG configuration error: {}").format(e))
        except KeyError as e:
            gs.fatal(_("Missing provider configuration: {}").format(e))


if __name__ == "__main__":
    options, flags = gs.parser()

    if EODAG_VERSION is None:
        gs.fatal(_("Cannot import eodag. Please install the library first."))

    if EODAG_VERSION not in (3, 4):
        gs.fatal(_("Only EODAG versions 3.x and 4.x are currently supported"))

    from eodag import EODataAccessGateway, setup_logging
    from eodag.api.search_result import SearchResult
    from eodag.utils.exceptions import MisconfiguredError

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
