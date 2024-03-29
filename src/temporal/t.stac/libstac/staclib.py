import grass.script as gs
from grass.pygrass.gis.region import Region
from grass.pygrass.vector import VectorTopo
from grass.pygrass.vector.geometry import Point, Area, Centroid, Boundary
import base64


def encode_credentials(username, password):
    """Encode username and password for basic authentication"""
    return base64.b64encode(f"{username}:{password}".encode("utf-8")).decode("utf-8")


def set_request_headers(**kwargs):
    """Set request headers"""
    username = kwargs.get("username")
    password = kwargs.get("password")
    token = kwargs.get("token")
    pl_subscription_key = kwargs.get("pc_subscription_key")

    req_headers = {}

    if (username and password) and token:
        raise ValueError("Provide either username and password or token, not both")

    if username and password:
        b64_userpass = encode_credentials(username, password)
        req_headers["Authorization"] = f"Basic {b64_userpass}"

    if token:
        req_headers["Authorization"] = f"Bearer {token}"

    if pl_subscription_key:
        req_headers["Ocp-Apim-Subscription-Key"] = pl_subscription_key

    return req_headers


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
