#!/usr/bin/env python3
##############################################################################
# MODULE:    v.in.ags
#
# AUTHOR(S): Corey T. White, NCSU GeoForAll Lab
#
# PURPOSE:   Import vector data from an ArcGIS Server (AGS) feature service
#            using the AGS REST API. Constructs the query URL automatically
#            and, by default, hands it to GDAL's ESRIJSON driver via v.import
#            (which auto-pages and reprojects to the project CRS). An optional
#            Esri Feature Buffer (PBF) fast path decodes features in-process.
#
# SPDX-FileCopyrightText: 2026 Corey White
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
##############################################################################

# %module
# % label: Imports vector data from an ArcGIS Server feature service.
# % description: Downloads features from an ArcGIS Server REST API endpoint \
#     and imports them as a GRASS vector map, reprojecting to the project CRS. \
#     Pagination is handled automatically.
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
# % required: no
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
# % options: input,region
# % label: Output vector map extent
# % descriptions: input;extent of input data;region;extent of current computational region
# % guisection: Selection
# %end

# %option
# % key: bbox_filter
# % type: string
# % required: no
# % label: Server-side bounding box filter (xmin,ymin,xmax,ymax in WGS84)
# % description: Comma-separated bounding box in geographic degrees (EPSG:4326) \
#     used to spatially filter features on the server before download.
# % guisection: Selection
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

# %option
# % key: spatial_rel
# % type: string
# % required: no
# % label: Spatial relationship used with the bounding box filter
# % description: ArcGIS Server spatial relationship constant that controls \
#     how features are matched against the bounding box. Only used with \
#     bbox_filter or extent=region.
# % options: esriSpatialRelIntersects,esriSpatialRelContains,esriSpatialRelCrosses,esriSpatialRelEnvelopeIntersects,esriSpatialRelIndexIntersects,esriSpatialRelOverlaps,esriSpatialRelTouches,esriSpatialRelWithin
# % answer: esriSpatialRelIntersects
# %end

# %option
# % key: order_by
# % type: string
# % required: no
# % label: ORDER BY fields
# % description: Comma-separated list of field names (optionally followed \
#     by ASC or DESC) that controls the order in which features are returned. \
#     Example: STATE_NAME ASC, POP2020 DESC
# %end

# %option
# % key: geometry_precision
# % type: integer
# % required: no
# % label: Number of decimal places for output coordinates
# % description: Limits coordinate precision in the downloaded data. \
#     Reduces transfer size at the cost of spatial accuracy. \
#     Leave unset to use the server default.
# %end

# %option
# % key: max_offset
# % type: double
# % required: no
# % label: Maximum allowable offset for geometry generalisation
# % description: Simplification tolerance in the output spatial reference \
#     units. Larger values produce fewer vertices. Leave unset to disable \
#     generalisation.
# %end

# %option
# % key: download_format
# % type: string
# % required: no
# % label: Feature download strategy
# % description: How features are fetched. auto and json read the service \
#     directly with GDAL's ESRIJSON driver (recommended); geojson uses GDAL's \
#     GeoJSON driver; pbf uses the built-in Esri Feature Buffer fast path.
# % options: auto,pbf,geojson,json
# % answer: auto
# %end

# %option
# % key: outsr
# % type: string
# % required: no
# % label: Output spatial reference (WKID) to request from the server
# % description: ArcGIS outSR well-known ID (e.g. 3358) for the downloaded \
#     data. Default is 4326 (WGS84); the result is reprojected to the project \
#     CRS on import. Ignored by the pbf download strategy.
# %end

# %option
# % key: snap
# % type: double
# % required: no
# % answer: -1
# % label: Snapping threshold for boundaries (map units)
# % description: '-1' for no snap. Use a small positive value to fix invalid \
#     polygon topology common in ArcGIS Server data.
# % guisection: Selection
# %end

# %option
# % key: datum_trans
# % type: integer
# % required: no
# % options: -1-100
# % label: Index number of datum transform parameters
# % description: -1 to list available datum transform parameters
# % guisection: Output
# %end

# %option G_OPT_F_FORMAT
# % options: plain,shell,json
# % descriptions: plain;Human readable text output;shell;Shell script style text output;json;JSON (JavaScript Object Notation)
# % guisection: Output
# %end

# %flag
# % key: l
# % description: List available layers in the service and exit without importing
# %end

# %flag
# % key: g
# % description: Skip geometry; import attribute table only
# %end

# %flag
# % key: o
# % label: Override projection check (use current project's CRS)
# % description: Assume that the dataset has the same CRS as the current project
# %end

# %rules
# % exclusive: extent, bbox_filter
# %end

import json
import shlex
import struct
import tempfile
import atexit
import gettext
from urllib.parse import urlencode

import grass.script as gs

_ = gettext.gettext

# Temporary files removed on exit
_TMP_FILES = []


def cleanup():
    """Remove temporary files created during the import session."""
    for path in _TMP_FILES:
        gs.try_remove(path)


# ─────────────────────────────────────────────────────────────────────────────
# HTTP helpers
# ─────────────────────────────────────────────────────────────────────────────


def _fetch_raw(url, timeout=120):
    """Fetch raw bytes from *url*.

    :param str url: URL to fetch.
    :param int timeout: Request timeout in seconds.
    :return: Response body as bytes.
    :rtype: bytes
    :raises SystemExit: On network or HTTP error.
    """
    import urllib.request
    import urllib.error

    gs.verbose(_("Fetching: '{}'").format(url))
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        gs.fatal(_("HTTP error {} fetching '{}': {}").format(exc.code, url, exc.reason))
    except urllib.error.URLError as exc:
        gs.fatal(_("Cannot connect to '{}': {}").format(url, str(exc.reason)))
    except OSError as exc:
        gs.fatal(_("Network error fetching '{}': {}").format(url, str(exc)))


def fetch_json(url, timeout=120):
    """Fetch and parse a JSON response from *url*.

    :param str url: URL to fetch.
    :param int timeout: Request timeout in seconds.
    :return: Parsed JSON object.
    :rtype: dict
    :raises SystemExit: On network, HTTP, or JSON error.
    """
    raw = _fetch_raw(url, timeout=timeout)
    try:
        return json.loads(raw.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        gs.fatal(_("Invalid JSON response from '{}': {}").format(url, str(exc)))


# ─────────────────────────────────────────────────────────────────────────────
# PBF (Esri Feature Buffer) decoder
# ─────────────────────────────────────────────────────────────────────────────


def _read_varint(data, pos):
    """Read a protobuf unsigned varint starting at *pos*.

    :param bytes data: Raw bytes buffer.
    :param int pos: Start offset.
    :return: (decoded value, new position).
    :rtype: tuple[int, int]
    """
    result = shift = 0
    while True:
        b = data[pos]
        pos += 1
        result |= (b & 0x7F) << shift
        if not (b & 0x80):
            break
        shift += 7
    return result, pos


def _zigzag(n):
    """Decode a zigzag-encoded unsigned integer to a signed integer.

    :param int n: Zigzag value.
    :rtype: int
    """
    return (n >> 1) ^ -(n & 1)


def _decode_packed_sint64(data):
    """Decode a packed repeated sint64 field (zigzag varints).

    :param bytes data: Packed field bytes.
    :return: List of signed int64 values.
    :rtype: list[int]
    """
    values = []
    pos = 0
    while pos < len(data):
        v, pos = _read_varint(data, pos)
        values.append(_zigzag(v))
    return values


def _decode_packed_uint32(data):
    """Decode a packed repeated uint32 field (plain varints).

    :param bytes data: Packed field bytes.
    :return: List of unsigned int32 values.
    :rtype: list[int]
    """
    values = []
    pos = 0
    while pos < len(data):
        v, pos = _read_varint(data, pos)
        values.append(v)
    return values


def _parse_pbf_message(data):
    """Deserialise raw protobuf *data* to a field-number → value mapping.

    Repeated fields are collected into lists.  Wire-type dispatch:

    - 0 (varint)           → ``int``
    - 1 (64-bit fixed)     → ``float`` (IEEE 754 double)
    - 2 (length-delimited) → ``bytes``
    - 5 (32-bit fixed)     → ``float`` (IEEE 754 single)

    :param bytes data: Raw protobuf message bytes.
    :return: Mapping of field number → value(s).
    :rtype: dict
    """
    result = {}
    pos = 0
    end = len(data)
    while pos < end:
        tag, pos = _read_varint(data, pos)
        field_num = tag >> 3
        wire_type = tag & 0x07

        if wire_type == 0:
            value, pos = _read_varint(data, pos)
        elif wire_type == 1:
            (value,) = struct.unpack_from("<d", data, pos)
            pos += 8
        elif wire_type == 2:
            length, pos = _read_varint(data, pos)
            value = bytes(data[pos : pos + length])
            pos += length
        elif wire_type == 5:
            (value,) = struct.unpack_from("<f", data, pos)
            pos += 4
        else:
            raise ValueError(
                "Unsupported protobuf wire type {} for field {}".format(
                    wire_type, field_num
                )
            )

        if field_num in result:
            existing = result[field_num]
            if isinstance(existing, list):
                existing.append(value)
            else:
                result[field_num] = [existing, value]
        else:
            result[field_num] = value
    return result


def _split_by_lengths(points, lengths):
    """Partition *points* into sub-lists according to *lengths*.

    :param list points: Flat list of coordinate tuples.
    :param list lengths: Sizes of successive sub-lists.
    :return: List of sub-lists.
    :rtype: list[list]
    """
    if not lengths:
        return [points]
    parts = []
    pos = 0
    for ln in lengths:
        parts.append(points[pos : pos + ln])
        pos += ln
    if pos < len(points):
        parts.append(points[pos:])
    return parts


def _ring_is_ccw(ring):
    """Return True when *ring* has counterclockwise winding (positive signed area).

    :param list ring: Sequence of (x, y) tuples.
    :rtype: bool
    """
    area = 0.0
    n = len(ring)
    for i in range(n):
        j = (i + 1) % n
        area += ring[i][0] * ring[j][1] - ring[j][0] * ring[i][1]
    return area > 0.0


def _close_ring(ring):
    """Return *ring* with the first point appended when it is not already closed.

    :param list ring: Sequence of (x, y) tuples.
    :rtype: list
    """
    if len(ring) < 3:
        return ring
    r = list(ring)
    if r[0] != r[-1]:
        r.append(r[0])
    return r


def _group_polygon_rings(parts):
    """Group flat polygon rings into ``[[exterior, *holes], ...]`` lists.

    Exterior rings are CCW (GeoJSON convention); holes are CW.  Rings that
    share winding with the first ring of the current polygon start a new
    polygon.

    :param list parts: Raw ring point lists from ``_split_by_lengths``.
    :return: List of polygons, each a list of closed rings.
    :rtype: list[list[list]]
    """
    polygons = []
    current = None
    for ring in parts:
        closed = _close_ring(ring)
        if not closed:
            continue
        is_ccw = _ring_is_ccw(closed)
        if current is None:
            current = [closed]
            current_outer_ccw = is_ccw
        elif is_ccw == current_outer_ccw:
            # Same winding as outer ring → new exterior ring → new polygon
            polygons.append(current)
            current = [closed]
            current_outer_ccw = is_ccw
        else:
            # Opposite winding → hole for current polygon
            current.append(closed)
    if current:
        polygons.append(current)
    return polygons or [[]]


def _decode_esri_geometry(geom_bytes, geom_type, xy_scale, x_origin, y_origin):
    """Decode an Esri Feature Buffer Geometry sub-message to a GeoJSON geometry.

    Coordinates are delta-decoded (the accumulator is NOT reset between
    rings/paths, following the Esri PBF convention) and de-quantised using
    the scale parameters when present.

    :param bytes geom_bytes: Raw Geometry sub-message bytes.
    :param int geom_type: EsriGeometryType enum (1=point, 2=multipoint,
        3=polyline, 4=polygon).
    :param float xy_scale: Quantization scale or ``None`` when raw floats.
    :param float x_origin: Quantization x-axis origin.
    :param float y_origin: Quantization y-axis origin.
    :return: GeoJSON geometry dict or ``None``.
    :rtype: dict or None
    """
    geom = _parse_pbf_message(geom_bytes)
    lengths = _decode_packed_sint64(geom.get(1, b""))
    raw_deltas = _decode_packed_sint64(geom.get(2, b""))

    # Accumulate delta-encoded quantized integers, then de-quantise.
    ix = iy = 0
    flat_pts = []
    for i in range(0, len(raw_deltas) - 1, 2):
        ix += raw_deltas[i]
        iy += raw_deltas[i + 1]
        if xy_scale:
            flat_pts.append((ix / xy_scale + x_origin, iy / xy_scale + y_origin))
        else:
            flat_pts.append((float(ix), float(iy)))

    # EsriGeometryType: 1=Point, 2=Multipoint, 3=Polyline, 4=Polygon
    if geom_type == 1:
        return {"type": "Point", "coordinates": list(flat_pts[0])} if flat_pts else None

    if geom_type == 2:
        return {"type": "MultiPoint", "coordinates": [list(p) for p in flat_pts]}

    if geom_type == 3:
        parts = _split_by_lengths(flat_pts, lengths)
        if len(parts) == 1:
            return {"type": "LineString", "coordinates": [list(p) for p in parts[0]]}
        return {
            "type": "MultiLineString",
            "coordinates": [[list(p) for p in pt] for pt in parts],
        }

    if geom_type == 4:
        effective_lengths = [abs(ln) for ln in lengths] if lengths else [len(flat_pts)]
        parts = _split_by_lengths(flat_pts, effective_lengths)
        polygons = _group_polygon_rings(parts)

        def rings_to_coords(poly):
            return [[list(p) for p in r] for r in poly]

        if len(polygons) == 1:
            return {"type": "Polygon", "coordinates": rings_to_coords(polygons[0])}
        return {
            "type": "MultiPolygon",
            "coordinates": [rings_to_coords(poly) for poly in polygons],
        }

    return None  # unsupported geometry type


def _decode_pbf_value(value_bytes):
    """Decode a single Esri Feature Buffer Value union sub-message.

    :param bytes value_bytes: Raw Value sub-message bytes.
    :return: Native Python scalar (str, float, int, bool, or None).
    """
    f = _parse_pbf_message(value_bytes)
    if 1 in f:  # string_value (bytes from length-delimited)
        raw = f[1]
        return raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
    if 2 in f:  # float_value (32-bit fixed → already decoded as float)
        return float(f[2])
    if 3 in f:  # double_value (64-bit fixed → already decoded as float)
        return float(f[3])
    if 4 in f:  # sint_value (sint32 – varint read raw, apply zigzag)
        return _zigzag(int(f[4]))
    if 5 in f:  # uint_value (uint32 varint)
        return int(f[5])
    if 6 in f:  # int64_value (varint, convert to signed)
        v = int(f[6])
        return v - (1 << 64) if v >= (1 << 63) else v
    if 7 in f:  # uint64_value (varint)
        return int(f[7])
    if 8 in f:  # sint64_value (sint64 – apply zigzag)
        return _zigzag(int(f[8]))
    if 9 in f:  # bool_value (varint)
        return bool(f[9])
    return None


def _pbf_to_geojson(pbf_bytes):
    """Decode an Esri Feature Buffer (PBF) response to a GeoJSON-compatible dict.

    The returned dict has the same structure as a GeoJSON FeatureCollection
    and can be passed to :func:`write_geojson` or merged across pagination pages.

    :param bytes pbf_bytes: Raw PBF response from an AGS ``/query`` call.
    :return: Dict with ``type``, ``features``, and ``exceededTransferLimit``.
    :rtype: dict
    :raises ValueError: If the binary cannot be decoded.
    """
    top = _parse_pbf_message(pbf_bytes)

    # Field 2 = queryResult embedded message
    qr_bytes = top.get(2)
    if not qr_bytes or not isinstance(qr_bytes, bytes):
        raise ValueError("PBF response missing queryResult (field 2)")
    qr = _parse_pbf_message(qr_bytes)

    # Field 1 of queryResult = featureResult embedded message
    fr_bytes = qr.get(1)
    if not fr_bytes or not isinstance(fr_bytes, bytes):
        raise ValueError("PBF queryResult missing featureResult (field 1)")
    fr = _parse_pbf_message(fr_bytes)

    geom_type = int(fr.get(7, 0))  # EsriGeometryType enum

    # Scale/quantization parameters (field 9 = Scale sub-message)
    xy_scale = x_origin = y_origin = None
    scale_bytes = fr.get(9)
    if scale_bytes and isinstance(scale_bytes, bytes):
        sc = _parse_pbf_message(scale_bytes)
        x_origin = float(sc.get(1, 0.0))
        y_origin = float(sc.get(2, 0.0))
        xy_scale = float(sc.get(3, 0.0)) or None  # treat 0 as "not set"

    exceeded = bool(fr.get(13, 0))

    # Field descriptors (field 10, repeated bytes)
    fd_list = fr.get(10, [])
    if isinstance(fd_list, bytes):
        fd_list = [fd_list]
    field_names = []
    for fb in fd_list:
        f = _parse_pbf_message(fb)
        name_raw = f.get(1, b"")
        field_names.append(
            name_raw.decode("utf-8") if isinstance(name_raw, bytes) else str(name_raw)
        )

    # Values pool (field 11, repeated bytes)
    val_list = fr.get(11, [])
    if isinstance(val_list, bytes):
        val_list = [val_list]
    values_pool = [_decode_pbf_value(vb) for vb in val_list]

    # Features (field 12, repeated bytes)
    feat_list = fr.get(12, [])
    if isinstance(feat_list, bytes):
        feat_list = [feat_list]

    geojson_features = []
    for feat_bytes in feat_list:
        feat = _parse_pbf_message(feat_bytes)

        # Attributes: packed uint32 indices into values_pool (field 1)
        attr_bytes = feat.get(1, b"")
        attr_indices = _decode_packed_uint32(attr_bytes) if attr_bytes else []
        properties = {
            field_names[i]: values_pool[idx]
            for i, idx in enumerate(attr_indices)
            if i < len(field_names) and idx < len(values_pool)
        }

        # Geometry (field 2)
        geom_bytes_feat = feat.get(2)
        geometry = None
        if geom_bytes_feat and isinstance(geom_bytes_feat, bytes):
            geometry = _decode_esri_geometry(
                geom_bytes_feat, geom_type, xy_scale, x_origin, y_origin
            )

        geojson_features.append(
            {"type": "Feature", "geometry": geometry, "properties": properties}
        )

    return {
        "type": "FeatureCollection",
        "features": geojson_features,
        "exceededTransferLimit": exceeded,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Service metadata helpers
# ─────────────────────────────────────────────────────────────────────────────


def normalize_url(url, layer_id):
    """Return a URL that ends with a numeric layer identifier.

    :param str url: ArcGIS Server URL (may or may not include a layer index).
    :param int layer_id: Layer index to append when one is absent.
    :return: Normalised layer URL.
    :rtype: str
    """
    url = url.rstrip("/")
    try:
        int(url.split("/")[-1])
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
    info = fetch_json("{}?{}".format(layer_url, urlencode({"f": "json"})))
    if "error" in info:
        gs.fatal(
            _("ArcGIS Server returned an error: {}").format(
                info["error"].get("message", "Unknown error")
            )
        )
    return info


def _format_layer_list(items, output_format):
    """Render a layer/table listing in the requested output format.

    :param list items: List of ``{"id", "type", "name"}`` dicts.
    :param str output_format: One of ``plain``, ``shell``, ``json``.
    :return: Formatted string ready to print.
    :rtype: str
    """
    if output_format == "json":
        return json.dumps(items, indent=4, ensure_ascii=False)
    if output_format == "shell":
        return "\n".join(
            "{}|{}|{}".format(it["id"], it["type"], it["name"]) for it in items
        )
    # plain: aligned table ("Feature Layer" is 13 chars, so the type column is 14)
    lines = [
        "{:<4} {:<14} {}".format("ID", "Type", "Name"),
        "{} {} {}".format("-" * 4, "-" * 14, "-" * 40),
    ]
    for it in items:
        lines.append(
            "{:<4} {:<14} {}".format(it["id"], str(it["type"])[:14], it["name"])
        )
    return "\n".join(lines)


def _format_layer_info(info, output_format):
    """Render single-layer metadata in the requested output format.

    :param dict info: Layer metadata (``id``, ``name``, ``geometry_type``,
        ``feature_count``, ``max_record_count``, ``supported_formats`` (list),
        ``fields`` (list)).
    :param str output_format: One of ``plain``, ``shell``, ``json``.
    :return: Formatted string ready to print.
    :rtype: str
    """
    if output_format == "json":
        return json.dumps(info, indent=4, ensure_ascii=False)

    fields_str = ",".join(info.get("fields", []))
    formats_str = ",".join(info.get("supported_formats", []))
    feature_count = info.get("feature_count")
    feature_count = "" if feature_count is None else feature_count

    if output_format == "shell":
        # Quote values so the output stays safely sourceable with `eval`
        # (layer names routinely contain spaces).
        lines = [
            "id={}".format(shlex.quote(str(info.get("id", "")))),
            "name={}".format(shlex.quote(str(info.get("name", "")))),
            "geometry_type={}".format(shlex.quote(str(info.get("geometry_type", "")))),
            "feature_count={}".format(shlex.quote(str(feature_count))),
            "max_record_count={}".format(
                shlex.quote(str(info.get("max_record_count", "")))
            ),
            "supported_formats={}".format(shlex.quote(formats_str)),
            "fields={}".format(shlex.quote(fields_str)),
        ]
        return "\n".join(lines)

    # plain: aligned label/value
    lines = [
        "{:<18} {}".format("ID:", info.get("id", "")),
        "{:<18} {}".format("Name:", info.get("name", "")),
        "{:<18} {}".format("Geometry type:", info.get("geometry_type", "")),
        "{:<18} {}".format("Feature count:", feature_count),
        "{:<18} {}".format("Max record count:", info.get("max_record_count", "")),
        "{:<18} {}".format("Supported formats:", formats_str),
        "{:<18} {}".format("Fields:", fields_str),
    ]
    return "\n".join(lines)


def list_layers(service_url, output_format="plain"):
    """Print the layers and tables available in a feature service.

    :param str service_url: URL of the FeatureServer or MapServer root.
    :param str output_format: One of ``plain``, ``shell``, ``json``.
    """
    base = service_url.rstrip("/")
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

    raw_items = info.get("layers", []) + info.get("tables", [])
    items = [
        {
            "id": item.get("id", "?"),
            "type": item.get("type", "Unknown"),
            "name": item.get("name", "Unknown"),
        }
        for item in raw_items
    ]
    if not items and output_format == "plain":
        gs.message(_("No layers or tables found at the given service URL."))
        return
    # For shell/json the empty case still emits valid machine output
    # (an empty JSON array / no lines) so downstream parsers do not break.
    print(_format_layer_list(items, output_format))


def describe_layer(
    layer_info,
    query_url,
    where,
    bbox,
    spatial_rel="esriSpatialRelIntersects",
    output_format="plain",
):
    """Print metadata for a single layer without importing it.

    :param dict layer_info: Service metadata from :func:`get_service_info`.
    :param str query_url: AGS query endpoint URL (for the feature count).
    :param str where: SQL WHERE expression.
    :param str bbox: Optional WGS84 bounding box or ``""``.
    :param str spatial_rel: Spatial relationship constant.
    :param str output_format: One of ``plain``, ``shell``, ``json``.
    """
    # The feature count needs an extra /query request; everything else is
    # already in hand from get_service_info. Treat a count failure as
    # non-fatal so the inspection still prints the rest of the metadata.
    try:
        count = get_feature_count(query_url, where, bbox, spatial_rel)
    except SystemExit:
        gs.warning(_("Could not determine the feature count for this layer."))
        count = None

    info = {
        "id": layer_info.get("id", ""),
        "name": layer_info.get("name", ""),
        "geometry_type": layer_info.get("geometryType", ""),
        "feature_count": count,
        "max_record_count": layer_info.get("maxRecordCount", ""),
        "supported_formats": [
            s.strip()
            for s in (layer_info.get("supportedQueryFormats") or "").split(",")
            if s.strip()
        ],
        "fields": [
            f.get("name", "")
            for f in (layer_info.get("fields") or [])
            if isinstance(f, dict)
        ],
    }
    print(_format_layer_info(info, output_format))


# ─────────────────────────────────────────────────────────────────────────────
# Query helpers
# ─────────────────────────────────────────────────────────────────────────────


def _apply_bbox(params, bbox, spatial_rel="esriSpatialRelIntersects"):
    """Add spatial-filter parameters to *params* when *bbox* is provided.

    :param dict params: Parameter dictionary to update in-place.
    :param str bbox: Bounding box ``xmin,ymin,xmax,ymax`` (WGS84) or ``""``.
    :param str spatial_rel: AGS spatial relationship constant.
    """
    if not bbox:
        return
    parts = [v.strip() for v in bbox.split(",")]
    if len(parts) != 4:
        gs.fatal(
            _(
                "Invalid bounding box '{}'. Expected xmin,ymin,xmax,ymax in WGS84."
            ).format(bbox)
        )
    xmin, ymin, xmax, ymax = parts
    params["geometry"] = "{},{},{},{}".format(xmin, ymin, xmax, ymax)
    params["geometryType"] = "esriGeometryEnvelope"
    params["inSR"] = "4326"
    params["spatialRel"] = spatial_rel


def build_query_url(
    query_url,
    where,
    fields,
    bbox,
    out_format="json",
    outsr="4326",
    geometry_precision=None,
    max_offset=None,
    order_by=None,
    return_geometry=True,
    spatial_rel="esriSpatialRelIntersects",
    offset=None,
    record_count=None,
):
    """Build a fully-encoded AGS ``/query`` URL from the request parameters.

    When *offset* is omitted the URL contains no ``resultOffset``, which lets
    GDAL's ESRIJSON/GeoJSON driver scroll through all pages automatically.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str fields: Comma-separated field names or ``*``.
    :param str bbox: Optional WGS84 bounding box or ``""``.
    :param str out_format: Server response format (``json`` or ``geojson``).
    :param str outsr: Output spatial reference WKID (default ``4326``).
    :param int geometry_precision: Coordinate decimal places or ``None``.
    :param float max_offset: Simplification tolerance or ``None``.
    :param str order_by: ORDER BY clause or ``None``.
    :param bool return_geometry: Include geometry in the response.
    :param str spatial_rel: Spatial relationship constant.
    :param int offset: Zero-based pagination offset or ``None``.
    :param int record_count: Records per page or ``None``.
    :return: Encoded request URL.
    :rtype: str
    """
    params = {
        "where": where,
        "outFields": fields,
        "outSR": outsr,
        "returnGeometry": "true" if return_geometry else "false",
        "f": out_format,
    }
    if offset is not None:
        params["resultOffset"] = offset
    if record_count is not None:
        params["resultRecordCount"] = record_count
    if geometry_precision is not None:
        params["geometryPrecision"] = int(geometry_precision)
    if max_offset is not None:
        params["maxAllowableOffset"] = max_offset
    if order_by:
        params["orderByFields"] = order_by
    _apply_bbox(params, bbox, spatial_rel)
    return "{}?{}".format(query_url, urlencode(params))


def get_feature_count(query_url, where, bbox, spatial_rel="esriSpatialRelIntersects"):
    """Return the number of features matching the query.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str bbox: Optional WGS84 bounding box or ``""``.
    :param str spatial_rel: Spatial relationship constant.
    :return: Total matching feature count.
    :rtype: int
    :raises SystemExit: If the server returns an error.
    """
    params = {"where": where, "f": "json", "returnCountOnly": "true"}
    _apply_bbox(params, bbox, spatial_rel)
    data = fetch_json("{}?{}".format(query_url, urlencode(params)))
    if "error" in data:
        gs.fatal(
            _("ArcGIS Server error counting features: {}").format(
                data["error"].get("message", "Unknown error")
            )
        )
    return data.get("count", 0)


def fetch_features_page(
    query_url,
    where,
    fields,
    bbox,
    offset,
    record_count,
    fmt="geojson",
    outsr="4326",
    geometry_precision=None,
    max_offset=None,
    order_by=None,
    return_geometry=True,
    spatial_rel="esriSpatialRelIntersects",
):
    """Download one page of features.

    Supports GeoJSON and Esri Feature Buffer (``pbf``).  PBF data is decoded
    on the fly to a GeoJSON-compatible dict so that callers always receive the
    same structure.

    :param str query_url: AGS query endpoint URL.
    :param str where: SQL WHERE expression.
    :param str fields: Comma-separated field names or ``*``.
    :param str bbox: Optional WGS84 bounding box or ``""``.
    :param int offset: Zero-based pagination offset.
    :param int record_count: Records per page.
    :param str fmt: One of ``pbf`` or ``geojson``.
    :param str outsr: Output spatial reference WKID (default ``4326``).
    :param int geometry_precision: Coordinate decimal places or ``None``.
    :param float max_offset: Simplification tolerance or ``None``.
    :param str order_by: ORDER BY clause or ``None``.
    :param bool return_geometry: Include geometry in response.
    :param str spatial_rel: Spatial relationship constant.
    :return: Dict with ``features`` list and optional ``exceededTransferLimit``.
    :rtype: dict
    :raises SystemExit: On server error.
    :raises ValueError: On PBF decoding failure (caller should retry with geojson).
    """
    url = build_query_url(
        query_url,
        where,
        fields,
        bbox,
        out_format=fmt,
        outsr=outsr,
        geometry_precision=geometry_precision,
        max_offset=max_offset,
        order_by=order_by,
        return_geometry=return_geometry,
        spatial_rel=spatial_rel,
        offset=offset,
        record_count=record_count,
    )

    if fmt == "pbf":
        raw = _fetch_raw(url)
        try:
            return _pbf_to_geojson(raw)
        except (IndexError, KeyError, struct.error) as exc:
            raise ValueError("PBF parse error: {}".format(exc)) from exc

    data = fetch_json(url)
    if "error" in data:
        gs.fatal(
            _("ArcGIS Server error fetching features: {}").format(
                data["error"].get("message", "Unknown error")
            )
        )
    return data


def fetch_all_features(
    query_url,
    where,
    fields,
    bbox,
    max_record_count,
    fmt="geojson",
    outsr="4326",
    geometry_precision=None,
    max_offset=None,
    order_by=None,
    return_geometry=True,
    spatial_rel="esriSpatialRelIntersects",
):
    """Download all matching features, paging through the service as needed.

    For ``pbf`` format, a PBF decode failure on the first page automatically
    triggers a retry with ``geojson`` for all subsequent pages.

    :return: ``(features, active_fmt)`` where *features* is a flat list of
        GeoJSON feature dicts and *active_fmt* is the format actually used.
    :rtype: tuple[list, str]
    """
    gs.message(_("Querying feature count..."))
    total_count = get_feature_count(query_url, where, bbox, spatial_rel)
    gs.message(_("Features matching query: {}.").format(total_count))

    if total_count == 0:
        return [], fmt

    active_fmt = fmt
    all_features = []
    offset = 0

    while offset < total_count:
        end = min(offset + max_record_count, total_count)
        gs.message(
            _("Downloading features {} to {} ({})...").format(
                offset + 1, end, active_fmt.upper()
            )
        )

        try:
            page = fetch_features_page(
                query_url,
                where,
                fields,
                bbox,
                offset,
                max_record_count,
                fmt=active_fmt,
                outsr=outsr,
                geometry_precision=geometry_precision,
                max_offset=max_offset,
                order_by=order_by,
                return_geometry=return_geometry,
                spatial_rel=spatial_rel,
            )
        except ValueError as exc:
            if active_fmt == "pbf":
                gs.warning(
                    _("PBF decoding failed ({}). Retrying with GeoJSON.").format(
                        str(exc)
                    )
                )
                active_fmt = "geojson"
                page = fetch_features_page(
                    query_url,
                    where,
                    fields,
                    bbox,
                    offset,
                    max_record_count,
                    fmt="geojson",
                    outsr=outsr,
                    geometry_precision=geometry_precision,
                    max_offset=max_offset,
                    order_by=order_by,
                    return_geometry=return_geometry,
                    spatial_rel=spatial_rel,
                )
            else:
                raise

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

        if not page.get("exceededTransferLimit", False):
            if len(page_features) < max_record_count:
                break

    gs.verbose(_("Total features downloaded: {}.").format(len(all_features)))
    return all_features, active_fmt


# ─────────────────────────────────────────────────────────────────────────────
# Output helpers
# ─────────────────────────────────────────────────────────────────────────────


def write_geojson(features, path):
    """Write *features* as a GeoJSON FeatureCollection to *path*.

    :param list features: List of GeoJSON feature dicts.
    :param str path: Destination file path.
    """
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(
            {"type": "FeatureCollection", "features": features},
            fh,
            ensure_ascii=False,
        )


def main():
    options, flags = gs.parser()

    url = options["url"].rstrip("/")
    output = options["output"]
    where = options["where"] if options["where"] else "1=1"
    fields = options["fields"] if options["fields"] else "*"
    vector_extent = options["extent"] or "input"
    bbox_filter = options["bbox_filter"]
    layer_id = int(options["layer"]) if options["layer"] else 0
    spatial_rel = options["spatial_rel"] or "esriSpatialRelIntersects"
    order_by = options["order_by"] or None
    geometry_precision = (
        int(options["geometry_precision"]) if options["geometry_precision"] else None
    )
    max_offset = float(options["max_offset"]) if options["max_offset"] else None
    preferred_fmt = options["download_format"] or "auto"
    requested_outsr = options["outsr"]
    snap = options["snap"]
    datum_trans = options["datum_trans"]
    output_format = options["format"]

    flag_list = flags["l"]
    flag_no_geom = flags["g"]
    flag_override = flags["o"]

    return_geometry = not flag_no_geom

    atexit.register(cleanup)

    # Layer-listing mode
    if flag_list:
        list_layers(url, output_format)
        return

    # Resolve the layer URL and query endpoint
    layer_url = normalize_url(url, layer_id)
    query_url = "{}/query".format(layer_url)

    # Resolve the server-side bounding-box filter. bbox_filter and extent=region
    # are mutually exclusive (enforced by the parser); extent=region derives the
    # WGS84 bbox of the current region so the download is limited at the server.
    if bbox_filter:
        bbox = bbox_filter
    elif vector_extent == "region":
        reg = gs.parse_command("g.region", flags="bg")
        bbox = "{},{},{},{}".format(reg["ll_w"], reg["ll_s"], reg["ll_e"], reg["ll_n"])
    else:
        bbox = ""

    # Layer-info mode: no output requested describe and exit.
    if not output:
        gs.message(_("Connecting to ArcGIS Server..."))
        layer_info = get_service_info(layer_url)
        describe_layer(
            layer_info,
            query_url,
            where,
            bbox,
            spatial_rel,
            output_format,
        )
        return

    # Output spatial reference requested from the server. Defaults to WGS84
    # (EPSG:4326); v.import reprojects to the current project CRS on import.
    # A user-supplied outsr lets the server reproject before download.
    outsr = requested_outsr if requested_outsr else "4326"

    if preferred_fmt == "pbf":
        # ------------------------------------------------------------------
        # Esri Feature Buffer fast path: download and decode PBF ourselves,
        # write a temporary GeoJSON, then import. The decoded output is written
        # as RFC-7946 GeoJSON (WGS84), so outsr cannot apply here.
        # ------------------------------------------------------------------
        if requested_outsr and requested_outsr != "4326":
            gs.warning(
                _("Option outsr is ignored for download_format=pbf; using EPSG:4326.")
            )

        gs.message(_("Connecting to ArcGIS Server..."))
        layer_info = get_service_info(layer_url)

        max_record_count = layer_info.get("maxRecordCount", 1000)
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

        features, _active_fmt = fetch_all_features(
            query_url,
            where,
            fields,
            bbox,
            max_record_count,
            fmt="pbf",
            outsr="4326",
            geometry_precision=geometry_precision,
            max_offset=max_offset,
            order_by=order_by,
            return_geometry=return_geometry,
            spatial_rel=spatial_rel,
        )

        if not features:
            gs.warning(
                _(
                    "No features were returned from the service. "
                    "The output vector map will not be created."
                )
            )
            return

        with tempfile.NamedTemporaryFile(suffix=".geojson", delete=False) as tmp_file:
            tmp_path = tmp_file.name
        _TMP_FILES.append(tmp_path)
        write_geojson(features, tmp_path)
        gs.verbose(_("Temporary GeoJSON written to '{}'.").format(tmp_path))
        datasource = tmp_path
    else:
        # Default: let GDAL read the service directly and auto-page
        out_format = "geojson" if preferred_fmt == "geojson" else "json"
        driver = "GeoJSON" if out_format == "geojson" else "ESRIJSON"
        full_url = build_query_url(
            query_url,
            where,
            fields,
            bbox,
            out_format=out_format,
            outsr=outsr,
            geometry_precision=geometry_precision,
            max_offset=max_offset,
            order_by=order_by,
            return_geometry=return_geometry,
            spatial_rel=spatial_rel,
        )
        datasource = "{}:{}".format(driver, full_url)
        gs.verbose(_("Reading service with GDAL: '{}'.").format(datasource))

    gs.message(_("Importing data and reprojecting to the project CRS..."))
    import_kwargs = {
        "input": datasource,
        "output": output,
        "extent": vector_extent,
        "snap": snap,
        "overwrite": gs.overwrite(),
    }
    if datum_trans:
        import_kwargs["datum_trans"] = datum_trans
    if flag_override:
        import_kwargs["flags"] = "o"
    gs.run_command("v.import", **import_kwargs)

    gs.vector_history(output)
    gs.message(_("Vector map <{}> successfully imported.").format(output))


if __name__ == "__main__":
    main()
