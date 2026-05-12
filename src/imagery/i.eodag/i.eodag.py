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
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from hashlib import md5
from pathlib import Path
from subprocess import PIPE

import grass.script as gs
from grass.pygrass.modules import Module


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
        # TODO: Might need to check for number of coordinates
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
        product = eodag_api.search(
            id=query_id,
            provider=module_options["provider"] or None,
            productType=module_options["producttype"] or None,
            count=True,
        )
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

    # Setting the envirionmnets variables has to come before the eodag initialization
    if config:
        config_file = Path(options["config"])
        if not config_file.is_file():
            gs.fatal(_("Config file '{}' not found.").format(options["config"]))
        env["EODAG_CFG_FILE"] = options["config"]


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
    columns = ["id", "startTimeFromAscendingNode", "cloudCover", "productType"]
    columns_na = ["id_NA", "time_NA", "cloudCover_NA", "productType_NA"]
    for product in products:
        product_line = ""
        for i, column in enumerate(columns):
            if column in product.properties:
                product_attribute_value = product.properties[column]
            else:
                product_attribute_value = None
            # Display NA if not available
            if product_attribute_value is None:
                product_attribute_value = columns_na[i]
            elif column == "cloudCover":
                # Special formatting for cloud cover
                product_attribute_value = f"{product_attribute_value:2.0f}%"
            elif column == "startTimeFromAscendingNode":
                # Special formatting for datetime
                try:
                    product_attribute_value = normalize_time(
                        product_attribute_value,
                    )
                except ValueError:
                    # Invalid ISO Format
                    gs.warning(
                        _("Timestamp {} is not compliant with ISO 8601").format(
                            product_attribute_value,
                        ),
                    )
                    product_attribute_value = product.properties[column]
            if i != 0:
                product_line += " "
            product_line += product_attribute_value
        print(product_line)


def list_products_json(products) -> None:
    """List products on the Standard Output stream (shell) in JSON format.

    :param products: EO poducts to be listed
    :type products: class:'eodag.api.search_result.SearchResult'
    """
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
    """Convert the start/end options to the isoformat and save them in-place.

    If options['end'] is not set, options['end'] will be today's date.
    If options['start'] is not set, options['start'] will be 60 days prior
    to options['end'] date.
    """
    end_date = options["end"]
    if not options["end"]:
        end_date = datetime.now(timezone.utc).isoformat()
    try:
        end_date = normalize_time(end_date)
    except ValueError as e:
        gs.debug(e)
        gs.fatal(_("Could not parse 'end' time."))

    start_date = options["start"]
    if not options["start"]:
        delta_days = timedelta(60)
        start_date = (datetime.fromisoformat(end_date) - delta_days).isoformat()
    try:
        start_date = normalize_time(start_date)
    except ValueError as e:
        gs.debug(e)
        gs.fatal(_("Could not parse 'start' time."))

    if end_date < start_date:
        gs.fatal(
            _("End Date <{}> can not come before start Date <{}>").format(
                end_date,
                start_date,
            ),
        )
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
            operator="le",
            cloudCover=int(cloud_cover),
        )

    # queryables are formatted as follow:
    # [('queryable_1' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ('queryable_2' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ('queryable_3' , [(value_1, operator_1), (value_2, operator_2), (value_3, operator_3), ...]),
    #  ...
    #  ...
    # ]
    if queryables:
        for queryable, values in queryables:
            if queryable in {"start", "end"}:
                continue
            tmp_search_result_list = []
            for value, operator in values:
                try:
                    filtered_search_result_list = search_result.filter_property(
                        operator=operator,
                        **{queryable: value},
                    ).data
                    tmp_search_result_list.extend(filtered_search_result_list)
                except TypeError:
                    gs.warning(
                        _(
                            "Invalid operator <{0}> for queryable <{1}>\n"
                            "Operator <{2}> will be used instead",
                        ).format(operator, queryable, default_operator),
                    )
                    filtered_search_result_list = search_result.filter_property(
                        operator=default_operator,
                        **{queryable: value},
                    ).data
                    tmp_search_result_list.extend(filtered_search_result_list)
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
    """Sorts search results according to options['sort'] and options['order'].

    options['sort'] parameters and options['order'] are matched correspondingly.
    If options['order'] parameters are not suffcient,
    'asc' will be used by default.

    :param search_result: EO products to be sorted
    :type search_result: class'eodag.api.search_result.SearchResult'

    :return: Sorted EO products
    :rtype: class:'eodag.api.search_result.SearchResult'
    """
    sort_keys = []
    for sort_key in options["sort"].split(","):
        if sort_key == "ingestiondate":
            sort_keys.append("startTimeFromAscendingNode")
        if sort_key == "title":
            sort_keys.append("title")
        if sort_key == "cloudcover":
            sort_keys.append("cloudCover")
    # Default values are used to put scenes with missing sorting key at the end
    search_result.sort(
        reverse=options["order"] == "desc",
        key=lambda product: [
            (
                (sort_key not in product.properties) ^ (options["order"] == "desc"),
                product.properties.get(sort_key, None),
            )
            for sort_key in sort_keys
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
                creation_time = str(
                    datetime.utcfromtimestamp(os.path.getctime(scene_file)),
                )
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
                    hashed_file = (
                        downloaded_dir
                        / md5(
                            (
                                scene.product_type + "-" + scene.properties["id"]
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
    gs.verbose(_("Saving searchin result in '{}'").format(file_name))
    eodag_api.serialize(search_result, filename=file_name)


def print_eodag_configuration(eodag_api, **kwargs) -> None:
    """Print EODAG currently recognized configurations in JSON format.

    :param provider: Print the configuration for only the given provider.
    :type provider: dict
    """
    provider = kwargs["provider"]

    def to_dict(config):
        """Convert EODAG configuration to a dictionary."""
        ret_dict = {}
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
        print(json.dumps(to_dict(eodag_api.providers_config[provider]), indent=4))
    else:
        print(json.dumps(to_dict(eodag_api.providers_config), indent=4))


def print_eodag_providers(eodag_api, **kwargs) -> None:
    """Print providers available in JSON format.

    :param kwargs: Restricts providers to providers offering specified product type.
    :type kwargs: dict
    """
    product_type = kwargs["producttype"]
    if product_type:
        gs.message(_("Recognized providers offering {}").format(product_type))
    else:
        gs.message(_("Recognized providers"))
    print(
        json.dumps(
            {"providers": eodag_api.available_providers(product_type or None)},
            indent=4,
        ),
    )


def print_eodag_products(eodag_api, **kwargs) -> None:
    """Print products available in JSON format.

    :param kwargs: Restricts products to products offered by specific provider
                   or specifies product type.
    :type kwargs: dict
    """
    provider = kwargs["provider"]
    product_type = kwargs["producttype"]
    if provider:
        gs.message(_("Recognized product types offered by {}").format(provider))
    else:
        gs.message(_("Recognized product types"))

    products = eodag_api.list_product_types(provider)
    if product_type:
        # Check for parial matches
        product_type_pattern = re.compile(
            re.escape(product_type),
            re.IGNORECASE,
        )
        products = [
            product
            for product in products
            if product_type_pattern.search(product["ID"])
        ]
    print(json.dumps({"products": products}, indent=4))


def print_eodag_queryables(eodag_api, **kwargs) -> None:
    """Print queryables info for given provider and/or product type in JSON format.

    :param kwargs: options/flags from gs.parser, with the crietria that will
                   be used for filtering.
    :type kwargs: dict
    """
    provider = kwargs["provider"]
    product_type = kwargs["producttype"]
    gs.message(_("Available queryables"))
    queryables = eodag_api.list_queryables(
        provider=provider or None,
        productType=product_type or None,
    )

    # Literal is for queryables that have a certain list of options to choose from.
    # Annotated is for queryables that accept a certain range e.g. cloudCover has range [0, 100].
    # TODO: It is assumed that if the type is Annotated, then the nested type will be int
    #       but that might not be the case.
    metadata_types = [
        "str",
        "int",
        "float",
        "dict",
        "list",
        "NoneType",
        "Literal",
        "Annotated",
    ]  # For testing and catching edge cases

    # Possible types to be passed through the query option
    # TODO: We can possibly extend the supported types
    supported_types = ["str", "int", "float", "Literal"]

    def get_type(info):
        potential_type = info.__args__[0]
        msg = "Unrecognized EODAG data type <>"
        if potential_type.__name__ != "Optional":
            if potential_type.__name__ not in metadata_types:
                raise AssertionError(msg.format(potential_type.__name__))
            return potential_type.__name__
        potential_type = potential_type.__args__[0]
        if potential_type.__name__ not in metadata_types:
            raise AssertionError(msg.format(potential_type.__name__))
        return potential_type.__name__

    def is_required(info):
        return info.__metadata__[0].is_required()

    def get_default(info):
        default = info.__metadata__[0].get_default()
        return default if isinstance(default, str) else "None"

    def get_options(info):
        return info.__args__[0].__args__

    def get_range(info):
        return (
            info.__args__[0].__args__[0].__metadata__[0].gt,
            info.__args__[0].__args__[0].__metadata__[1].lt,
        )

    queryables_dict = {}
    for queryable, info in queryables.items():
        queryable_dict = {
            "required": is_required(info),
            "default": get_default(info),
        }
        try:
            queryable_dict["type"] = get_type(info)
        except AssertionError as e:
            gs.debug(e)
            gs.warning(
                "Unrecognized EODAG product type detected. Please report this issue, if accessible.",
            )
            continue
        if queryable_dict["type"] == "Literal":
            # There is a restricted list of options to choose from
            queryable_dict["options"] = get_options(info)
        if queryable_dict["type"] == "Annotated":
            # There is a range for the queryable
            queryable_dict["type"] = "int"
            queryable_dict["range"] = get_range(info)
        if queryable_dict["type"] == "NoneType":
            queryable_dict["type"] = "str"
        if queryable_dict["type"] in supported_types:
            queryables_dict[queryable] = queryable_dict

    queryables_dict.pop("geom", None)
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
    # Products: https://github.com/CS-SI/eodag/blob/develop/eodag/resources/product_types.yml

    setup_environment_variables(os.environ, **options, **flags)
    dag = EODataAccessGateway()

    # Check provider input
    provider = None
    if options["provider"]:
        # If no provider is given available providers are searched according to configured
        # priorities, however, currently search in multiple providers at once is not supported
        # Check for when this feature is added https://github.com/CS-SI/eodag/issues/163
        if options["provider"] not in dag.available_providers():
            gs.fatal(_("Provider {} not available.").format(options["provider"]))
        dag.set_preferred_provider(options["provider"])
        provider = options["provider"]

    # Get AOI
    geometry = get_aoi(options["map"])
    gs.verbose(_("AOI: {}").format(geometry))

    # Check producttype input

    if options["producttype"] and options["producttype"] not in {
        p["ID"] for p in dag.list_product_types(provider)
    }:
        gs.fatal(
            _("Product type <{}> not available.").format(options["producttype"]),
        )

    # Get queryables
    queryables = parse_query(options["query"])
    for queryable, values in queryables:
        if queryable == "start":
            if options["start"]:
                gs.fatal(_("Queryable <start> can not be set twice"))
            # there will only be one value in the values, values[0][0] is the date
            options["start"] = values[0][0]
        if queryable == "end":
            if options["end"]:
                gs.fatal(_("Queryable <end> can not be set twice"))
            # there will only be one value in the values, values[0][0] is the date
            options["end"] = values[0][0]

    # Setup print function if requested
    if options["print"]:
        print_functions = {
            "providers": print_eodag_providers,
            "products": print_eodag_products,
            "config": print_eodag_configuration,
            "queryables": print_eodag_queryables,
        }
        print_functions[options["print"]](dag, **options)
        return

    if flags["p"]:
        print_query(geometry, queryables, **options)
        return

    # Perform initial search or load previous search results
    id_file = Path(options["file"]) if options["file"] else None
    if id_file and not id_file.is_file():
        gs.fatal(_('Could not open file "{}"').format(options["file"]))

    if options["id"]:  # Parse IDs
        search_result = search_by_ids(
            {pid.strip() for pid in options["id"].split(",")},
            options,
            eodag_api=dag,
        )
    elif id_file and id_file.suffix.lower() == ".geojson":
        gs.verbose(
            _("Reading stored search result from file <{}>").format(options["file"]),
        )
        # Read saved EODAG search result from GeoJSON file
        try:
            search_result = dag.deserialize_and_register(options["file"])
        except RuntimeError as e:
            gs.error(_(e))
            gs.fatal(
                _(
                    "File '{}' could not be read by EODAG, file content is probably altered.",
                ).format(options["file"]),
            )
    elif id_file and id_file.suffix.lower() == ".txt":
        # Read IDs from TEXT file
        try:
            search_result = search_by_ids(
                {
                    pid.strip()
                    for pid in id_file.read_text(encoding="UTF8").strip().split("\n")
                },
                options,
                eodag_api=dag,
            )
        except OSError:
            gs.fatal(
                _(
                    "Unable to read product IDs from file <{}>.",
                ).format(options["file"]),
            )
    elif id_file:
        gs.fatal(
            _(
                "File type '{}' is not supported. Please use a '.geojson' or '.txt' file.",
            ).format(id_file.suffix.lower()),
        )
    else:
        # Search using given search parameters
        dates_to_iso_format()
        # TODO: Check that the product_type exists
        # could be handled by catching exceptions when searching...
        product_type = options["producttype"]

        search_parameters = {
            "productType": product_type,
            "geom": geometry,
            "provider": provider,
        }

        if options["clouds"]:
            search_parameters["cloudCover"] = options["clouds"]

        search_parameters["start"] = options["start"]
        search_parameters["end"] = options["end"]
        if not options["area_relation"]:
            options["area_relation"] = "Intersects"

        # Conduct parameter search
        search_result = dag.search_all(**search_parameters)

        gs.verbose(_("Filtering results..."))
        search_result = filter_result(
            search_result,
            geometry if "geometry" in locals() else None,
            queryables,
            **options,
        )

    # Remove duplictes that might be created while filtering
    search_result = remove_duplicates(search_result)

    # Check if search results were downloaded before
    if flags["s"]:
        search_result = skip_existing(options["output"], search_result)

    gs.verbose(_("Sorting results..."))
    search_result = sort_result(search_result)

    if options["limit"] and not (options["id"] or options["file"]):
        search_result = SearchResult(search_result[: int(options["limit"])])

    if options["footprints"]:
        save_footprints(search_result, options["footprints"], dag)

    gs.verbose(_("{} scene(s) found.").format(len(search_result)))

    # Save search results
    if options["save"]:
        save_search_result(search_result, options["save"], dag)

    if flags["l"]:
        list_products(search_result)
    elif flags["j"]:
        list_products_json(search_result)
    else:
        # TODO: Consider adding a quicklook flag
        try:
            # TODO: Would be better if we could find a way to not ask the user for the OTP manually
            providers = (scene.provider for scene in search_result)
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
                    dag.providers_config["creodias"].auth.credentials["totp"] = (
                        creodias_otp
                    )
                    dag._plugins_manager.get_auth_plugin("creodias").authenticate()
            custom_config = {
                "timeout": int(options["timeout"]),
                "wait": int(options["wait"]),
            }
            if not search_result:
                gs.message(_("Nothing to download.\nExiting..."))
            if options["output"]:
                custom_config["output_dir"] = options["output"]
            dag.download_all(search_result, **custom_config)
        except MisconfiguredError as e:
            gs.fatal(_(e))


if __name__ == "__main__":
    options, flags = gs.parser()

    try:
        import eodag

        if int(eodag.__version__.split(".")[0]) != 3:
            gs.fatal(_("Only EODAG version 3.x is currently supported"))
        from eodag import EODataAccessGateway, setup_logging
        from eodag.api.search_result import SearchResult
        from eodag.utils.exceptions import MisconfiguredError
    except ImportError:
        gs.fatal(_("Cannot import eodag. Please install the library first."))

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
