import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point, Area, Centroid, Boundary
import base64
import tempfile
import json
import os
from pystac_client.conformance import ConformanceClasses
from pystac_client.exceptions import APIError


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
    n_matched = None
    try:
        n_matched = search.matched()
    except Exception:
        gs.verbose(_("STAC API doesn't support matched() method."))

    if n_matched:
        pages = (n_matched // max_items) + 1
    else:
        # These requests tend to be very slow
        pages = len(list(search.pages()))

    gs.message(_(f"Fetching items {n_matched} from {pages} pages."))

    feature_collection = {"type": "FeatureCollection", "features": []}

    # Extract asset information for each item
    for page in range(pages):
        temp_features = search.item_collection_as_dict()
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

    if n_matched:
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


def get_all_collections(client):
    """Get a list of collections from STAC Client"""
    if conform_to_collections(client):
        gs.verbose(_("Client conforms to Collection"))
    try:
        collections = client.get_collections()
        collection_list = list(collections)
        return [i.to_dict() for i in collection_list]

    except APIError as e:
        gs.fatal(_("Error getting collections: {}".format(e)))


def _check_conformance(client, conformance_class, response="fatal"):
    """Check if the STAC API conforms to the given conformance class"""
    if not client.conforms_to(conformance_class):
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


def conform_to_collections(client):
    """Check if the STAC API conforms to the Collections conformance class"""
    return _check_conformance(client, ConformanceClasses.COLLECTIONS)


def conform_to_item_search(client):
    """Check if the STAC API conforms to the Item Search conformance class"""
    return _check_conformance(client, ConformanceClasses.ITEM_SEARCH)


def conform_to_filter(client):
    """Check if the STAC API conforms to the Filter conformance class"""
    return _check_conformance(client, ConformanceClasses.FILTER)


def conform_to_query(client):
    """Check if the STAC API conforms to the Query conformance class"""
    return _check_conformance(client, ConformanceClasses.QUERY)


def conform_to_sort(client):
    """Check if the STAC API conforms to the Sort conformance class"""
    return _check_conformance(client, ConformanceClasses.SORT)


def conform_to_fields(client):
    """Check if the STAC API conforms to the Fields conformance class"""
    return _check_conformance(client, ConformanceClasses.FIELDS)


def conform_to_core(client):
    """Check if the STAC API conforms to the Core conformance class"""
    return _check_conformance(client, ConformanceClasses.CORE)


def conform_to_context(client):
    """Check if the STAC API conforms to the Context conformance class"""
    return _check_conformance(client, ConformanceClasses.CONTEXT)
