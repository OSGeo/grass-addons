#!/usr/bin/env python3
##############################################################################
# MODULE:    v.in.ags
#
# AUTHOR(S): Corey White <ctwhite448 at gmail com>
#
# PURPOSE:   Import vector data from an ArcGIS Server (AGS) feature service
#            using the AGS REST API. Constructs the query URL automatically
#            and delegates import to v.in.ogr or v.import.
#
# COPYRIGHT: (C) 2024 by Corey White and the GRASS Development Team
#
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % label: Imports vector data from an ArcGIS Server feature service.
# % description: Downloads features from an ArcGIS Server REST API endpoint \
#     and imports them as a GRASS vector map. Handles pagination automatically. \
#     Use -r to reproject data to the current project CRS.
# % keyword: vector
# % keyword: import
# % keyword: ArcGIS Server
# % keyword: REST API
# % keyword: OGR
# %end

# %option
# % key: url
# % type: string
# % required: yes
# % label: ArcGIS Server feature layer URL
# % description: URL of the ArcGIS Server FeatureServer or MapServer layer \
#     (e.g., https://host/arcgis/rest/services/Name/FeatureServer/0). \
#     If a service root URL is given (without a layer index), use the layer option.
# %end

# %option G_OPT_V_OUTPUT
# %end

# %option
# % key: where
# % type: string
# % required: no
# % label: SQL WHERE clause to filter features
# % description: SQL expression used to select a subset of features. \
#     Default is 1=1 which selects all features.
# % answer: 1=1
# %end

# %option
# % key: fields
# % type: string
# % required: no
# % label: Comma-separated list of fields to retrieve
# % description: Attribute fields to include in the output. \
#     Use * to retrieve all fields (default).
# % answer: *
# %end

# %option
# % key: extent
# % type: string
# % required: no
# % label: Bounding box spatial filter (xmin,ymin,xmax,ymax in WGS84)
# % description: Comma-separated bounding box in geographic degrees \
#     (EPSG:4326) used to spatially filter features before download.
# %end

# %option
# % key: layer
# % type: integer
# % required: no
# % label: Layer index within the service
# % description: Zero-based layer index to use when the URL points to a \
#     FeatureServer or MapServer root rather than a specific layer endpoint.
# % answer: 0
# %end

# %flag
# % key: r
# % description: Reproject data to match the current GRASS project CRS (uses v.import)
# %end

# %flag
# % key: l
# % description: List available layers in the service and exit without importing
# %end

import json
import tempfile
import atexit
import gettext
from urllib.parse import urlencode

import grass.script as gs

_ = gettext.gettext

# Temporary files to clean up on exit
_TMP_FILES = []


def cleanup():
    """Remove temporary files created during the import session."""
    for path in _TMP_FILES:
        gs.try_remove(path)


def fetch_json(url, timeout=30):
    """Fetch and parse a JSON response from *url*.

    :param str url: URL to fetch.
    :param int timeout: Request timeout in seconds.
    :return: Parsed JSON object.
    :rtype: dict
    :raises SystemExit: On network error or HTTP error.
    """
    import urllib.request
    import urllib.error

    gs.verbose(_("Fetching URL: '{}'").format(url))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        gs.fatal(_("HTTP error {} fetching '{}': {}").format(exc.code, url, exc.reason))
    except urllib.error.URLError as exc:
        gs.fatal(_("Cannot connect to '{}': {}").format(url, str(exc.reason)))
    except OSError as exc:
        gs.fatal(_("Network error fetching '{}': {}").format(url, str(exc)))

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        gs.fatal(_("Invalid JSON response from '{}': {}").format(url, str(exc)))


def normalize_url(url, layer_id):
    """Return a URL that ends with a numeric layer identifier.

    If *url* already ends with an integer (e.g., `.../FeatureServer/0`),
    it is returned unchanged.  Otherwise *layer_id* is appended.

    :param str url: ArcGIS Server URL (may or may not include a layer index).
    :param int layer_id: Layer index to append when one is absent.
    :return: Normalised layer URL.
    :rtype: str
    """
    url = url.rstrip("/")
    try:
        int(url.split("/")[-1])
        # Last segment is already an integer – URL already has a layer id.
        return url
    except ValueError:
        return "{}/{}".format(url, layer_id)


def get_service_info(layer_url):
    """Retrieve metadata for an ArcGIS Server layer.

    :param str layer_url: URL of the feature or map layer.
    :return: Service metadata dictionary.
    :rtype: dict
    :raises SystemExit: If the server returns an error response.
    """
    info_url = "{}?{}".format(layer_url, urlencode({"f": "json"}))
    info = fetch_json(info_url)
    if "error" in info:
        gs.fatal(
            _("ArcGIS Server returned an error: {}").format(
                info["error"].get("message", "Unknown error")
            )
        )
    return info


def list_layers(service_url):
    """Print a table of layers and tables available in a feature service.

    :param str service_url: URL of the FeatureServer or MapServer root.
    """
    base = service_url.rstrip("/")
    # Strip a trailing layer id so we reach the service root.
    try:
        int(base.split("/")[-1])
        base = "/".join(base.split("/")[:-1])
    except ValueError:
        pass

    info = fetch_json("{}?{}".format(base, urlencode({"f": "json"})))
    if "error" in info:
        gs.fatal(
            _("ArcGIS Server returned an error: {}").format(
                info["error"].get("message", "Unknown error")
            )
        )

    layers = info.get("layers", [])
    tables = info.get("tables", [])
    all_items = layers + tables

    if not all_items:
        gs.message(_("No layers or tables found at the given service URL."))
        return

    gs.message("{:<4} {:<12} {}".format("ID", "Type", "Name"))
    gs.message("{} {} {}".format("-" * 4, "-" * 12, "-" * 40))
    for item in all_items:
        gs.message(
            "{:<4} {:<12} {}".format(
                item.get("id", "?"),
                item.get("type", "Unknown")[:12],
                item.get("name", "Unknown"),
            )
        )


def get_feature_count(query_url, where, extent):
    """Return the number of features matching the given filter.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str extent: Optional bounding box ``xmin,ymin,xmax,ymax`` or ``""``.
    :return: Total matching feature count.
    :rtype: int
    :raises SystemExit: If the server returns an error.
    """
    params = {
        "where": where,
        "f": "json",
        "returnCountOnly": "true",
    }
    _apply_extent(params, extent)

    data = fetch_json("{}?{}".format(query_url, urlencode(params)))
    if "error" in data:
        gs.fatal(
            _("ArcGIS Server error counting features: {}").format(
                data["error"].get("message", "Unknown error")
            )
        )
    return data.get("count", 0)


def _apply_extent(params, extent):
    """Add spatial-filter parameters to *params* when *extent* is provided.

    :param dict params: Parameter dictionary to update in-place.
    :param str extent: Bounding box string ``xmin,ymin,xmax,ymax`` or ``""``.
    """
    if not extent:
        return
    parts = [v.strip() for v in extent.split(",")]
    if len(parts) != 4:
        gs.fatal(
            _(
                "Invalid extent format: '{}'. Expected xmin,ymin,xmax,ymax in WGS84."
            ).format(extent)
        )
    xmin, ymin, xmax, ymax = parts
    params["geometry"] = "{},{},{},{}".format(xmin, ymin, xmax, ymax)
    params["geometryType"] = "esriGeometryEnvelope"
    params["inSR"] = "4326"
    params["spatialRel"] = "esriSpatialRelIntersects"


def fetch_features_page(query_url, where, fields, extent, offset, record_count):
    """Download one page of features in GeoJSON format.

    All geometry is requested in WGS84 (EPSG:4326) so that the resulting
    GeoJSON file complies with RFC 7946 and can be reliably passed to
    *v.in.ogr* or *v.import*.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str fields: Comma-separated field names or ``*``.
    :param str extent: Optional bounding box string or ``""``.
    :param int offset: Zero-based pagination offset.
    :param int record_count: Number of records to request on this page.
    :return: GeoJSON FeatureCollection dict for this page.
    :rtype: dict
    :raises SystemExit: If the server returns an error response.
    """
    params = {
        "where": where,
        "outFields": fields,
        "outSR": "4326",
        "f": "geojson",
        "returnGeometry": "true",
        "resultOffset": offset,
        "resultRecordCount": record_count,
    }
    _apply_extent(params, extent)

    data = fetch_json("{}?{}".format(query_url, urlencode(params)), timeout=120)
    if "error" in data:
        gs.fatal(
            _("ArcGIS Server error fetching features: {}").format(
                data["error"].get("message", "Unknown error")
            )
        )
    return data


def fetch_all_features(query_url, where, fields, extent, max_record_count):
    """Download all matching features, paging through the service as needed.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str fields: Comma-separated field names or ``*``.
    :param str extent: Optional bounding box string or ``""``.
    :param int max_record_count: Maximum records the service returns per page.
    :return: Flat list of GeoJSON feature dicts.
    :rtype: list
    """
    gs.message(_("Querying feature count..."))
    total_count = get_feature_count(query_url, where, extent)
    gs.message(_("Features matching query: {}.").format(total_count))

    if total_count == 0:
        return []

    all_features = []
    offset = 0

    while offset < total_count:
        end = min(offset + max_record_count, total_count)
        gs.message(_("Downloading features {} to {}...").format(offset + 1, end))

        page = fetch_features_page(
            query_url, where, fields, extent, offset, max_record_count
        )
        page_features = page.get("features", [])

        if not page_features:
            gs.warning(
                _(
                    "Server returned no features at offset {}. "
                    "Download may be incomplete."
                ).format(offset)
            )
            break

        all_features.extend(page_features)
        offset += len(page_features)

        # Some servers set exceededTransferLimit when more records exist.
        if not page.get("exceededTransferLimit", False):
            if len(page_features) < max_record_count:
                # Received a partial page – no more records remain.
                break

    gs.verbose(_("Total features downloaded: {}.").format(len(all_features)))
    return all_features


def write_geojson(features, path):
    """Serialise *features* to a GeoJSON FeatureCollection file at *path*.

    :param list features: List of GeoJSON feature dicts.
    :param str path: Destination file path.
    """
    collection = {
        "type": "FeatureCollection",
        "features": features,
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(collection, fh, ensure_ascii=False)


def main():
    options, flags = gs.parser()

    url = options["url"].rstrip("/")
    output = options["output"]
    where = options["where"] if options["where"] else "1=1"
    fields = options["fields"] if options["fields"] else "*"
    extent = options["extent"]
    layer_id = int(options["layer"]) if options["layer"] else 0
    flag_reproject = flags["r"]
    flag_list = flags["l"]

    atexit.register(cleanup)

    # ------------------------------------------------------------------
    # Layer-listing mode: print table and exit without importing.
    # ------------------------------------------------------------------
    if flag_list:
        list_layers(url)
        return

    # ------------------------------------------------------------------
    # Resolve the layer URL and query endpoint.
    # ------------------------------------------------------------------
    layer_url = normalize_url(url, layer_id)
    query_url = "{}/query".format(layer_url)

    # ------------------------------------------------------------------
    # Fetch service metadata.
    # ------------------------------------------------------------------
    gs.message(_("Connecting to ArcGIS Server..."))
    layer_info = get_service_info(layer_url)

    max_record_count = layer_info.get("maxRecordCount", 1000)
    # Guard against unusably large page sizes (some services report 0).
    if max_record_count <= 0:
        max_record_count = 1000

    supports_pagination = layer_info.get("advancedQueryCapabilities", {}).get(
        "supportsPagination", True
    )
    if not supports_pagination:
        gs.warning(
            _(
                "This service does not advertise pagination support. "
                "Only the first {} features will be imported."
            ).format(max_record_count)
        )

    layer_name = layer_info.get("name", "unknown")
    gs.verbose(
        _("Layer: '{}', max record count: {}.").format(layer_name, max_record_count)
    )

    # ------------------------------------------------------------------
    # Download all matching features.
    # ------------------------------------------------------------------
    features = fetch_all_features(query_url, where, fields, extent, max_record_count)

    if not features:
        gs.warning(
            _(
                "No features were returned from the service. "
                "The output vector map will not be created."
            )
        )
        return

    # ------------------------------------------------------------------
    # Write features to a temporary GeoJSON file.
    # ------------------------------------------------------------------
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".geojson", delete=False, encoding="utf-8"
    ) as tmp_file:
        tmp_path = tmp_file.name
    _TMP_FILES.append(tmp_path)
    write_geojson(features, tmp_path)
    gs.verbose(_("Temporary GeoJSON written to '{}'.").format(tmp_path))

    # ------------------------------------------------------------------
    # Import: v.import reprojects; v.in.ogr imports as-is (WGS84).
    # ------------------------------------------------------------------
    if flag_reproject:
        gs.message(_("Importing and reprojecting to project CRS with v.import..."))
        gs.run_command(
            "v.import",
            input=tmp_path,
            output=output,
            overwrite=gs.overwrite(),
        )
    else:
        gs.message(_("Importing data with v.in.ogr (data in WGS84)..."))
        gs.run_command(
            "v.in.ogr",
            input=tmp_path,
            output=output,
            overwrite=gs.overwrite(),
        )

    gs.vector_history(output)
    gs.message(_("Vector map <{}> successfully imported.").format(output))


if __name__ == "__main__":
    main()
