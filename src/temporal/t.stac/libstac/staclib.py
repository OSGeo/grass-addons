#!/usr/bin/env python3

############################################################################
#
# MODULE:       staclib
# AUTHOR:       Corey T. White, OpenPlains Inc. & NCSU
# PURPOSE:      Helper library to import STAC data in to GRASS.
# COPYRIGHT:    (C) 2024 Corey White
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################


import os
import base64
import tempfile
import json
import grass.script as gs
from grass.exceptions import CalledModuleError
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point, Centroid, Boundary
from concurrent.futures import ThreadPoolExecutor

# Import pystac_client modules
try:
    from pystac_client import Client
    from pystac_client.exceptions import APIError
    from pystac_client.conformance import ConformanceClasses
except ImportError as err:
    gs.fatal(_("Unable to import pystac_client: {err}"))


def _import_tqdm(error):
    """Import tqdm module"""
    try:
        from tqdm import tqdm

        return tqdm
    except ImportError as err:
        if error:
            raise err
        return None


def _import_pystac_mediatype(error):
    """Import pystac module"""
    try:
        from pystac import MediaType

        return MediaType
    except ImportError as err:
        if error:
            raise err
        return None


class STACHelper:
    """STAC Helper Class"""

    def __init__(self):
        self.client = None

    def connect_to_stac(self, url, headers=None):
        """Connect to a STAC catalog."""
        if self.client is None:
            try:
                self.client = Client.open(url, headers)
                return self.client
            except APIError as err:
                gs.fatal(f"Failed to connect to STAC catalog: {err}")
        else:
            gs.warning(_("Client already connected."))
            return self.client

    def get_all_collections(self):
        """Get a list of collections from STAC Client"""
        if self.conforms_to_collections():
            gs.verbose(_("Client conforms to Collection"))
        try:
            collections = self.client.get_collections()
            collection_list = list(collections)
            return [i.to_dict() for i in collection_list]

        except APIError as e:
            gs.fatal(_("Error getting collections: {}".format(e)))

    def get_collection(self, collection_id):
        """Get a collection from STAC Client"""
        try:
            collection = self.client.get_collection(collection_id)
            self.collection = collection.to_dict()
            return self.collection

        except APIError as e:
            gs.fatal(_("Error getting collection: {}".format(e)))

    def search_api(self, **kwargs):
        """Search the STAC API"""
        if self.conforms_to_item_search():
            gs.verbose(_("STAC API Conforms to Item Search"))

        if kwargs.get("filter"):
            self.conforms_to_filter()

        if kwargs.get("query"):
            self.conforms_to_query()

        try:
            search = self.client.search(**kwargs)
        except APIError as e:
            gs.fatal(_("Error searching STAC API: {}".format(e)))
        except NotImplementedError as e:
            gs.fatal(_("Error searching STAC API: {}".format(e)))
        except Exception as e:
            gs.fatal(_("Error searching STAC API: {}".format(e)))

        try:
            gs.message(_(f"Search Matched: {search.matched()} items"))
        except e:
            gs.warning(_(f"No items found: {e}"))
            return None

        return search

    def report_stac_item(self, item):
        """Print a report of the STAC item to the console."""
        gs.message(_(f"Collection ID: {item.collection_id}"))
        gs.message(_(f"Item: {item.id}"))
        print_attribute(item, "geometry", "Geometry")
        gs.message(_(f"Bbox: {item.bbox}"))

        print_attribute(item, "datetime", "Datetime")
        print_attribute(item, "start_datetime", "Start Datetime")
        print_attribute(item, "end_datetime", "End Datetime")
        gs.message(_("Extra Fields:"))
        print_summary(item.extra_fields)

        print_list_attribute(item.stac_extensions, "Extensions:")
        # libstac.print_attribute(it_import_tqdmem, "stac_extensions", "Extensions")
        gs.message(_("Properties:"))
        print_summary(item.properties)

    def _check_conformance(self, conformance_class, response="fatal"):
        """Check if the STAC API conforms to the given conformance class"""
        if not self.client.conforms_to(conformance_class):
            if response == "fatal":
                gs.fatal(_(f"STAC API does not conform to {conformance_class}"))
                return False
            elif response == "warning":
                gs.warning(_(f"STAC API does not conform to {conformance_class}"))
                return True
            elif response == "verbose":
                gs.verbose(_(f"STAC API does not conform to {conformance_class}"))
                return True
            elif response == "info":
                gs.info(_(f"STAC API does not conform to {conformance_class}"))
                return True
            elif response == "message":
                gs.message(_(f"STAC API does not conform to {conformance_class}"))
                return True

    def conforms_to_collections(self):
        """Check if the STAC API conforms to the Collections conformance class"""
        return self._check_conformance(ConformanceClasses.COLLECTIONS)

    def conforms_to_item_search(self):
        """Check if the STAC API conforms to the Item Search conformance class"""
        return self._check_conformance(ConformanceClasses.ITEM_SEARCH, "warning")

    def conforms_to_filter(self):
        """Check if the STAC API conforms to the Filter conformance class"""
        return self._check_conformance(ConformanceClasses.FILTER, response="warning")

    def conforms_to_query(self):
        """Check if the STAC API conforms to the Query conformance class"""
        return self._check_conformance(ConformanceClasses.QUERY, response="warning")

    def conforms_to_sort(self):
        """Check if the STAC API conforms to the Sort conformance class"""
        return self._check_conformance(ConformanceClasses.SORT)

    def conforms_to_fields(self):
        """Check if the STAC API conforms to the Fields conformance class"""
        return self._check_conformance(ConformanceClasses.FIELDS)

    def conforms_to_core(self):
        """Check if the STAC API conforms to the Core conformance class"""
        return self._check_conformance(ConformanceClasses.CORE)

    def conforms_to_context(self):
        """Check if the STAC API conforms to the Context conformance class"""
        return self._check_conformance(ConformanceClasses.CONTEXT)


def encode_credentials(username, password):
    """Encode username and password for basic authentication"""
    return base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")


def set_request_headers(settings):
    """Set request headers"""
    req_headers = {}
    username = password = None
    if settings == "-":
        # stdin
        import getpass

        username = input(_("Insert username: "))
        password = getpass.getpass(_("Insert password: "))

    elif settings:
        try:
            with open(settings, "r") as fd:
                lines = list(
                    filter(None, (line.rstrip() for line in fd))
                )  # non-blank lines only
                if len(lines) < 2:
                    gs.fatal(_("Invalid settings file"))
                username = lines[0].strip()
                password = lines[1].strip()

        except IOError as e:
            gs.fatal(_("Unable to open settings file: {}").format(e))
    else:
        return req_headers

    if username is None or password is None:
        gs.fatal(_("No user or password given"))

    if username and password:
        b64_userpass = encode_credentials(username, password)
        req_headers["Authorization"] = f"Basic {b64_userpass}"

    return req_headers


def generate_indentation(depth):
    """Generate indentation for summary"""
    return "    " * depth


def print_summary(data, depth=1):
    """Print summary of json data recursively increasing indentation."""
    start_depth = depth
    for key, value in data.items():
        indentation = generate_indentation(start_depth)
        if isinstance(value, dict):
            gs.message(_(f"#\n# {indentation}{key}:"))
            print_summary(value, depth=start_depth + 1)
        if isinstance(value, list):
            gs.message(_(f"# {indentation}{key}:"))
            for item in value:
                if isinstance(item, dict):
                    print_summary(item, depth=start_depth + 1)
        else:
            gs.message(_(f"# {indentation}{key}: {value}"))


def print_list_attribute(data, title):
    "Print a list attribute"
    gs.message(_(f"{title}"))
    for item in data:
        gs.message(_(f"\t{item}"))


def print_attribute(item, attribute, message=None):
    """Print an attribute of the item and handle AttributeError."""
    message = message if message else attribute.capitalize()
    try:
        gs.message(_(f"{message}: {getattr(item, attribute)}"))
    except AttributeError:
        gs.info(_(f"{message} not found."))


def print_basic_collection_info(collection):
    """Print basic information about a collection"""
    gs.message(_(f"Collection ID: {collection.get('id')}"))
    gs.message(_(f"STAC Version: {collection.get('stac_version')}"))
    gs.message(_(f"Description: {collection.get('description')}"))
    gs.message(_(f"Extent: {collection.get('extent')}"))
    gs.message(_(f"License: {collection.get('license')}"))
    gs.message(_(f"Keywords: {collection.get('keywords')}"))
    item_summary = collection.get("summaries")
    gs.message(_(f"{'-' * 75}\n"))
    if item_summary:
        gs.message(_("Summary:"))
        for k, v in item_summary.items():
            gs.message(_(f"{k}: {v}"))
        gs.message(_(f"{'-' * 75}\n"))
    item_assets = collection.get("item_assets")
    item_asset_keys = item_assets.keys()

    gs.message(_(f"Item Assets Keys: {list(item_asset_keys)}"))
    gs.message(_(f"{'-' * 75}\n"))
    for key, value in item_assets.items():
        gs.message(_(f"Asset: {value.get('title')}"))
        gs.message(_(f"Key: {key}"))
        gs.message(_(f"Roles: {value.get('roles')}"))
        gs.message(_(f"Type: {value.get('type')}"))
        gs.message(_(f"Description: {value.get('description')}"))
        if value.get("gsd"):
            gs.message(_(f"GSD: {value.get('gsd')}"))
        if value.get("eo:bands"):
            gs.message(_("EO Bands:"))
            for band in value.get("eo:bands"):
                gs.message(_(f"Band: {band}"))
        if value.get("proj:shape"):
            gs.message(_(f"Shape: {value.get('proj:shape')}"))
        if value.get("proj:transform"):
            gs.message(_(f"Asset Transform: {value.get('proj:transform')}"))
        if value.get("proj:crs"):
            gs.message(_(f"CRS: {value.get('proj:crs')}"))
        if value.get("proj:geometry"):
            gs.message(_(f"Geometry: {value.get('proj:geometry')}"))
        if value.get("proj:extent"):
            gs.message(_(f"Asset Extent: {value.get('proj:extent')}"))
        if value.get("raster:bands"):
            gs.message(_("Raster Bands:"))
            for band in value.get("raster:bands"):
                gs.message(_(f"Band: {band}"))

        gs.message(_(f"{'-' * 75}\n"))


def collection_metadata(collection):
    """Get collection"""

    gs.message(_("*" * 80))
    gs.message(_(f"Collection Id: {collection.get('id')}"))
    gs.message(_(f"Title: {collection.get('title')}"))
    gs.message(_(f"Description: {collection.get('description')}"))

    extent = collection.get("extent")
    if extent:
        spatial = extent.get("spatial")
        if spatial:
            bbox = spatial.get("bbox")
            if bbox:
                gs.message(_(f"bbox: {bbox}"))
        temporal = extent.get("temporal")
        if temporal:
            interval = temporal.get("interval")
            if interval:
                gs.message(_(f"Temporal Interval: {interval}"))

    gs.message(_(f"License: {collection.get('license')}"))
    gs.message(_(f"Keywords: {collection.get('keywords')}"))
    # gs.message(_(f"Providers: {collection.get('providers')}"))
    gs.message(_(f"Links: {collection.get('links')}"))
    gs.message(_(f"Stac Extensions: {collection.get('stac_extensions')}"))

    try:
        gs.message(_("\n# Summaries:"))
        print_summary(collection.get("summaries"))
    except AttributeError:
        gs.info(_("Summaries not found."))

    try:
        gs.message(_("\n# Extra Fields:"))
        print_summary(collection.get("extra_fields"))
    except AttributeError:
        gs.info(_("# Extra Fields not found."))
    gs.message(_("*" * 80))


def report_plain_asset_summary(asset):
    MediaType = _import_pystac_mediatype(False)
    gs.message(_("\nAsset"))
    gs.message(_(f"Asset Item Id: {asset.get('item_id')}"))

    gs.message(_(f"Asset Title: {asset.get('title')}"))
    gs.message(_(f"Asset Filename: {asset.get('file_name')}"))
    gs.message(_(f"Raster bands: {asset.get('raster:bands')}"))
    gs.message(_(f"Raster bands: {asset.get('eo:bands')}"))
    gs.message(_(f"Asset Description: {asset.get('description')}"))

    if MediaType:
        gs.message(_(f"Asset Media Type: { MediaType(asset.get('type')).name}"))
    else:
        gs.message(_(f"Asset Media Type: {asset.get('type')}"))
    gs.message(_(f"Asset Roles: {asset.get('roles')}"))
    gs.message(_(f"Asset Href: {asset.get('href')}"))


def region_to_wgs84_decimal_degrees_bbox():
    """convert region bbox to wgs84 decimal degrees bbox"""
    region = gs.parse_command("g.region", quiet=True, flags="ubg")
    bbox = [
        float(c)
        for c in [region["ll_w"], region["ll_s"], region["ll_e"], region["ll_n"]]
    ]
    gs.message(_("BBOX: {}".format(bbox)))
    return bbox


def check_url_type(url):
    """
    Check if the URL is 's3://', 'gs://', or 'http(s)://'.

    Parameters:
    - url (str): The URL to check.

    Returns:
    - str: 's3', 'gs', 'http', or 'unknown' based on the URL type.
    """
    if url.startswith("s3://"):
        os.environ["AWS_PROFILE"] = "default"
        os.environ["AWS_REQUEST_PAYER"] = "requester"
        return url.replace("s3://", "/vsis3/")  # Amazon S3
    elif url.startswith("gs://"):
        return url.replace("gs://", "/vsigs/")  # Google Cloud Storage
    elif url.startswith("abfs://"):
        return url.replace("abfs://", "/vsiaz/")  # Azure Blob File System
    elif url.startswith("https://"):
        return url.replace("https://", "/vsicurl/https://")
        # TODO: Add check for cloud provider that uses https
        # return url.replace("https://", "/vsiaz/")  # Azure Blob File System
        # return url
    elif url.startswith("http://"):
        gs.warning(_("HTTP is not secure. Using HTTPS instead."))
        return url.replace("https://", "/vsicurl/https://")
    else:
        gs.message(_(f"Unknown Protocol: {url}"))
        return "unknown"


def bbox_to_nodes(bbox):
    """
    Convert a bounding box to polygon coordinates.

    Parameters:
    bbox (dict): A dictionary with 'west', 'south', 'east', 'north' keys.

    Returns:
    list of tuples: Coordinates of the polygon [(lon, lat), ...].
    """
    w, s, e, n = bbox["west"], bbox["south"], bbox["east"], bbox["north"]
    # Define corners: bottom-left, top-left, top-right, bottom-right, close by returning to start
    corners = [Point(w, s), Point(w, n), Point(e, n), Point(e, s), Point(w, s)]
    return corners


def wgs84_bbox_to_boundary(bbox):
    """
    Reprojects WGS84 bbox to the current locations CRS.

    Args:
        bbox (list): A list containing the WGS84 bounding box coordinates in the order (west, south, east, north).

    Returns:
        dict: A dictionary containing the coordinates in the order (west, south, east, north).

    Example:
        >>> bbox = [-122.5, 37.5, -122, 38]
        >>> wgs84_bbox_to_boundary(bbox)
        {'west': -122.5, 'south': 37.5, 'east': -122, 'north': 38}
    """

    west, south, east, north = bbox

    # Reproject to location projection
    min_coords = gs.read_command(
        "m.proj",
        coordinates=(west, south),
        separator="comma",
        flags="i",
    )

    max_coords = gs.read_command(
        "m.proj",
        coordinates=(east, north),
        separator="comma",
        flags="i",
    )

    min_list = min_coords.split(",")[:2]
    max_list = max_coords.split(",")[:2]

    # Concatenate the lists
    list_bbox = min_list + max_list
    west, south, east, north = list_bbox
    dict_bbox = {"west": west, "south": south, "east": east, "north": north}

    return dict_bbox


def safe_float_cast(value):
    """Attempt to cast a value to float, return None if not possible."""
    try:
        return float(value)
    except ValueError:
        return None


def polygon_centroid(polygon_coords):
    """
    Create a centroid for a given polygon.

    Args:
        polygon_coords (list(Point)): List of coordinates representing the polygon.

    Returns:
        Centroid: The centroid of the polygon.

    """
    # Calculate the sums of the x and y coordinates
    sum_x = sum(
        point.x for point in polygon_coords[:-1]
    )  # Exclude the last point if it's a repeat
    sum_y = sum(point.y for point in polygon_coords[:-1])
    num_points = len(polygon_coords) - 1

    # Calculate the averages for x and y
    centroid_x = sum_x / num_points
    centroid_y = sum_y / num_points
    # Create a centroid for the boundary to make it an area
    centroid = Centroid(x=centroid_x, y=centroid_y)
    return centroid


def _flatten_dict(d, parent_key="", sep="_"):
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(_flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def create_vector_from_feature_collection(vector, search, limit, max_items):
    """Create a vector from items in a Feature Collection"""

    feature_collection = {"type": "FeatureCollection", "features": []}

    # Extract asset information for each item
    for page in search.pages_as_dicts():
        temp_features = page
        for idx, item in enumerate(temp_features["features"]):
            flattened_assets = _flatten_dict(
                item["assets"], parent_key="assets", sep="."
            )
            temp_features["features"][idx]["properties"].update(flattened_assets)
            temp_features["features"][idx]["properties"]["collection"] = item[
                "collection"
            ]
        feature_collection["features"].extend(temp_features["features"])

    json_str = json.dumps(feature_collection)
    with tempfile.NamedTemporaryFile(delete=True, suffix=".json") as fp:
        fp.write(bytes(json_str, "utf-8"))
        fp.truncate()
        gs.run_command(
            "v.import", input=fp.name, output=vector, overwrite=True, quiet=True
        )
        fp.close()

    gs.run_command("v.colors", map=vector, color="random", quiet=True)


def register_strds_from_items(collection_items_assets, strds_output):
    """Create registy for STRDS from collection items assets"""
    with open(strds_output, "w") as f:
        for asset in collection_items_assets:
            semantic_label = asset.get("file_name").split(".")[-1]
            created_date = asset.get("datetime")

            if created_date:
                f.write(f"{asset['file_name']}|{created_date}|{semantic_label}\n")
            else:
                gs.warning(_("No datetime found for item."))
                f.write(f"{asset['file_name']}|{None}|{semantic_label}\n")


def fetch_items_with_pagination(items_search, limit, max_items):
    """
    Fetches items from a search result with pagination.

    Args:
        items_search (SearchResult): The search result object.
        limit (int): The maximum number of items to fetch.
        max_items (int): The maximum number of items on a page.

    Returns:
        list: A list of items fetched from the search result.
    """
    items = []
    n_matched = None
    try:
        n_matched = items_search.matched()
    except Exception:
        gs.verbose(_("STAC API doesn't support matched() method."))

    if n_matched and max_items is not None:
        pages = (n_matched // max_items) + 1
    else:
        # These requests tend to be very slow
        pages = len(list(items_search.pages()))

    for page in range(pages):
        page_items = items_search.items()
        for item in page_items:
            items.append(item)
        if len(items) >= limit:
            break

    return items


def create_metadata_vector(vector, metadata):
    """Create a vector map from metadata"""

    COLS = [
        ("cat", "INTEGER PRIMARY KEY"),
        ("id", "TEXT"),
        ("title", "TEXT"),
        ("type", "TEXT"),
        # (u'description', 'TEXT'),
        ("startdate", "TEXT"),
        ("enddate", "TEXT"),
        ("license", "TEXT"),
        ("stac_version", "TEXT"),
        ("keywords", "TEXT"),
    ]

    with VectorTopo(
        vector, mode="w", tab_cols=COLS, layer=1, overwrite=True
    ) as new_vec:

        for i, item in enumerate(metadata):
            gs.message(_("Adding collection: {}".format(item.get("id"))))
            # Transform bbox to locations CRS
            # Safe extraction
            extent = item.get("extent", {})
            spatial = extent.get("spatial", {})
            temporal = extent.get("temporal", {})
            interval = temporal.get("interval", [])
            if interval and isinstance(interval, list):
                start_datetime, end_datetime = interval[0]
            else:
                start_datetime = None
                end_datetime = None

            bbox_list = spatial.get("bbox", [])
            # Ensure bbox_list is not empty and has the expected structure
            if bbox_list and isinstance(bbox_list[0], list) and len(bbox_list[0]) == 4:
                wgs84_bbox = bbox_list[0]
            else:
                gs.warning(
                    _("Invalid bbox. Skipping Collection {}.".format(item.get("id")))
                )
                continue

            bbox = wgs84_bbox_to_boundary(wgs84_bbox)

            # Iterate over the list of dictionaries and attempt to cast each value to float using safe_float_cast
            if not all(safe_float_cast(i) for i in bbox.values()):
                gs.warning(
                    _("Invalid bbox. Skipping Collection {}.".format(item.get("id")))
                )
                continue

            # Cast all values to float
            for key, value in bbox.items():
                bbox[key] = safe_float_cast(value)

            # Convert the bbox to polygon coordinates
            polygon_coords = bbox_to_nodes(bbox)
            boundary = Boundary(points=polygon_coords)

            # Create centroid from the boundary
            centroid = polygon_centroid(polygon_coords)

            # area = Area(polygon_coords)
            new_vec.write(centroid)
            new_vec.write(
                geo_obj=boundary,
                cat=i + 1,
                attrs=(
                    item.get("id"),
                    item.get("title"),
                    item.get("type"),
                    # item.get("description"),
                    start_datetime,
                    end_datetime,
                    item.get("license"),
                    item.get("stac_version"),
                    ",".join(item.get("keywords")),
                ),
            )
        new_vec.table.conn.commit()
        new_vec.build()

    return metadata


def import_grass_raster(params):
    assets, resample_method, extent, resolution, resolution_value, memory = params
    gs.message(_(f"Downloading Asset: {assets}"))
    input_url = check_url_type(assets["href"])
    gs.message(_(f"Import Url: {input_url}"))

    try:
        gs.message(_(f"Importing: {assets['file_name']}"))
        gs.parse_command(
            "r.import",
            input=input_url,
            output=assets["file_name"],
            resample=resample_method,
            extent=extent,
            resolution=resolution,
            resolution_value=resolution_value,
            title=assets["file_name"],
            memory=memory,
            quiet=True,
        )
    except CalledModuleError as e:
        gs.fatal(_("Error importing raster: {}".format(e.stderr)))


def download_assets(
    assets,
    resample_method,
    resample_extent,
    resolution,
    resolution_value,
    memory=300,
    nprocs=1,
):
    """Downloads a list of images from the given URLs to the given filenames."""
    number_of_assets = len(assets)
    resample_extent_list = [resample_extent] * number_of_assets
    resolution_list = [resolution] * number_of_assets
    resolution_value_list = [resolution_value] * number_of_assets
    resample_method_list = [resample_method] * number_of_assets
    memory_list = [memory] * number_of_assets
    max_cpus = os.cpu_count() - 1
    if nprocs > max_cpus:
        gs.warning(
            _(
                "Number of processes {nprocs} is greater than the number of CPUs {max_cpus}."
            )
        )
        nprocs = max_cpus

    def execute_import_grass_raster(pbar=None):
        with ThreadPoolExecutor(max_workers=nprocs) as executor:
            try:
                for _a in executor.map(
                    import_grass_raster,
                    zip(
                        assets,
                        resample_method_list,
                        resample_extent_list,
                        resolution_list,
                        resolution_value_list,
                        memory_list,
                    ),
                ):
                    if pbar:
                        pbar.update(1)
            except Exception as e:
                gs.fatal(_("Error importing raster: {}".format(str(e))))

    tqdm = _import_tqdm(False)
    if tqdm is None:
        gs.warning(_("tqdm module not found. Progress bar will not be displayed."))
        execute_import_grass_raster()
    else:
        with tqdm(total=number_of_assets, desc="Downloading assets") as pbar:
            execute_import_grass_raster(pbar)
