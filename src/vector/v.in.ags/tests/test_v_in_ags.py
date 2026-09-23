"""Tests for v.in.ags

Unit tests exercise the helper functions (URL normalisation, spatial-filter
parameter construction, JSON/GeoJSON writing, PBF decoding, format selection,
feature counting) using mocked HTTP calls so no network connection is required.

Integration tests verify end-to-end behaviour against a real ArcGIS Server.
They are skipped automatically when the network is unavailable or no GRASS
environment is active.

Run (no GRASS needed for unit tests):
    python -m pytest tests/test_v_in_ags.py -v

Or with gunittest inside a GRASS session:
    python -m grass.gunittest.main --config .gunittest.cfg
"""

import json
import os
import struct
import sys
import tempfile
import unittest
from unittest.mock import patch

# ---------------------------------------------------------------------------
# Load the module without triggering the GRASS parser.
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import importlib
import importlib.util
import types

_MODULE_PATH = os.path.join(os.path.dirname(__file__), "..", "v.in.ags.py")


def _load_module():
    """Load v.in.ags helper functions without executing main()."""
    spec = importlib.util.spec_from_file_location("v_in_ags", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)

    # Minimal grass.script stub
    gs_stub = types.ModuleType("grass.script")
    gs_stub.fatal = lambda msg: (_ for _ in ()).throw(SystemExit(msg))
    gs_stub.warning = lambda msg: None
    gs_stub.message = lambda msg: None
    gs_stub.verbose = lambda msg: None
    gs_stub.try_remove = lambda path: None
    gs_stub.overwrite = lambda: False
    gs_stub.vector_history = lambda name: None
    gs_stub.run_command = lambda *a, **kw: None
    sys.modules.setdefault("grass", types.ModuleType("grass"))
    sys.modules["grass.script"] = gs_stub

    spec.loader.exec_module(mod)
    return mod


_mod = _load_module()


# ===========================================================================
# URL normalisation
# ===========================================================================


class TestNormalizeUrl(unittest.TestCase):
    def test_url_with_layer_id_unchanged(self):
        url = "https://host/arcgis/rest/services/Svc/FeatureServer/0"
        self.assertEqual(_mod.normalize_url(url, 99), url)

    def test_trailing_slash_stripped(self):
        url = "https://host/arcgis/rest/services/Svc/FeatureServer/0/"
        self.assertEqual(_mod.normalize_url(url, 99), url.rstrip("/"))

    def test_layer_id_appended(self):
        base = "https://host/arcgis/rest/services/Svc/FeatureServer"
        self.assertEqual(_mod.normalize_url(base, 3), base + "/3")

    def test_layer_id_zero_appended(self):
        base = "https://host/arcgis/rest/services/Svc/FeatureServer"
        self.assertEqual(_mod.normalize_url(base, 0), base + "/0")


# ===========================================================================
# Spatial filter parameter builder
# ===========================================================================


class TestApplyExtent(unittest.TestCase):
    def test_empty_extent_no_change(self):
        params = {}
        _mod._apply_bbox(params, "")
        self.assertEqual(params, {})

    def test_none_extent_no_change(self):
        params = {}
        _mod._apply_bbox(params, None)
        self.assertEqual(params, {})

    def test_valid_extent_populates_params(self):
        params = {}
        _mod._apply_bbox(params, "-125,42,-116,49")
        self.assertEqual(params["geometry"], "-125,42,-116,49")
        self.assertEqual(params["geometryType"], "esriGeometryEnvelope")
        self.assertEqual(params["inSR"], "4326")
        self.assertEqual(params["spatialRel"], "esriSpatialRelIntersects")

    def test_custom_spatial_rel(self):
        params = {}
        _mod._apply_bbox(params, "-125,42,-116,49", "esriSpatialRelContains")
        self.assertEqual(params["spatialRel"], "esriSpatialRelContains")

    def test_spaces_in_extent_trimmed(self):
        params = {}
        _mod._apply_bbox(params, " -125 , 42 , -116 , 49 ")
        self.assertEqual(params["geometry"], "-125,42,-116,49")

    def test_invalid_extent_raises(self):
        with self.assertRaises(SystemExit):
            _mod._apply_bbox({}, "invalid,extent")


# ===========================================================================
# Query URL builder
# ===========================================================================


class TestBuildQueryUrl(unittest.TestCase):
    def test_basic_params_present(self):
        url = _mod.build_query_url(
            "https://h/q", "1=1", "STATE_NAME,POP", "", out_format="json"
        )
        self.assertTrue(url.startswith("https://h/q?"))
        self.assertIn("where=1%3D1", url)
        self.assertIn("outFields=STATE_NAME%2CPOP", url)
        self.assertIn("outSR=4326", url)
        self.assertIn("f=json", url)
        self.assertIn("returnGeometry=true", url)

    def test_geojson_format(self):
        url = _mod.build_query_url("https://h/q", "1=1", "*", "", out_format="geojson")
        self.assertIn("f=geojson", url)

    def test_custom_outsr(self):
        url = _mod.build_query_url("https://h/q", "1=1", "*", "", outsr="3358")
        self.assertIn("outSR=3358", url)

    def test_no_offset_by_default(self):
        # No resultOffset lets GDAL auto-page.
        url = _mod.build_query_url("https://h/q", "1=1", "*", "")
        self.assertNotIn("resultOffset", url)

    def test_offset_and_record_count_included(self):
        url = _mod.build_query_url(
            "https://h/q", "1=1", "*", "", offset=200, record_count=100
        )
        self.assertIn("resultOffset=200", url)
        self.assertIn("resultRecordCount=100", url)

    def test_optional_params(self):
        url = _mod.build_query_url(
            "https://h/q",
            "1=1",
            "*",
            "",
            geometry_precision=4,
            max_offset=0.5,
            order_by="NAME ASC",
            return_geometry=False,
        )
        self.assertIn("geometryPrecision=4", url)
        self.assertIn("maxAllowableOffset=0.5", url)
        self.assertIn("orderByFields=NAME+ASC", url)
        self.assertIn("returnGeometry=false", url)

    def test_extent_spatial_filter(self):
        url = _mod.build_query_url(
            "https://h/q",
            "1=1",
            "*",
            "-125,42,-116,49",
            spatial_rel="esriSpatialRelContains",
        )
        self.assertIn("geometryType=esriGeometryEnvelope", url)
        self.assertIn("esriSpatialRelContains", url)


# ===========================================================================
# GeoJSON file writer
# ===========================================================================


class TestWriteGeoJson(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
        self._tmp.close()
        self._path = self._tmp.name

    def tearDown(self):
        if os.path.exists(self._path):
            os.unlink(self._path)

    def test_valid_feature_collection(self):
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-120, 45]},
                "properties": {"name": "Test"},
            }
        ]
        _mod.write_geojson(features, self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 1)

    def test_empty_feature_collection(self):
        _mod.write_geojson([], self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["features"], [])

    def test_unicode_preserved(self):
        features = [
            {"type": "Feature", "geometry": None, "properties": {"n": "São Paulo"}}
        ]
        _mod.write_geojson(features, self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["features"][0]["properties"]["n"], "São Paulo")


# ===========================================================================
# PBF low-level helpers
# ===========================================================================


class TestVarint(unittest.TestCase):
    def _encode_varint(self, n):
        """Encode *n* as a protobuf unsigned varint."""
        out = []
        while True:
            bits = n & 0x7F
            n >>= 7
            if n:
                out.append(bits | 0x80)
            else:
                out.append(bits)
                break
        return bytes(out)

    def test_small_value(self):
        data = self._encode_varint(1)
        val, pos = _mod._read_varint(data, 0)
        self.assertEqual(val, 1)
        self.assertEqual(pos, 1)

    def test_multibyte_value(self):
        data = self._encode_varint(300)
        val, pos = _mod._read_varint(data, 0)
        self.assertEqual(val, 300)

    def test_zigzag_positive(self):
        self.assertEqual(_mod._zigzag(0), 0)
        self.assertEqual(_mod._zigzag(2), 1)
        self.assertEqual(_mod._zigzag(4), 2)

    def test_zigzag_negative(self):
        self.assertEqual(_mod._zigzag(1), -1)
        self.assertEqual(_mod._zigzag(3), -2)
        self.assertEqual(_mod._zigzag(5), -3)


class TestDecodePacked(unittest.TestCase):
    def _zigzag_encode(self, n):
        return (n << 1) ^ (n >> 63) if n >= 0 else ((-n - 1) << 1) | 1

    def _encode_varint(self, n):
        out = []
        while True:
            bits = n & 0x7F
            n >>= 7
            if n:
                out.append(bits | 0x80)
            else:
                out.append(bits)
                break
        return bytes(out)

    def _pack_sint64(self, values):
        return b"".join(self._encode_varint(self._zigzag_encode(v)) for v in values)

    def test_decode_sint64(self):
        data = self._pack_sint64([5, -3, 100, -1])
        result = _mod._decode_packed_sint64(data)
        self.assertEqual(result, [5, -3, 100, -1])

    def test_decode_uint32(self):
        data = (
            self._encode_varint(0) + self._encode_varint(3) + self._encode_varint(255)
        )
        result = _mod._decode_packed_uint32(data)
        self.assertEqual(result, [0, 3, 255])


class TestParsePbfMessage(unittest.TestCase):
    def _make_message(self, field_num, wire_type, value_bytes):
        """Build a minimal one-field protobuf message."""
        tag = (field_num << 3) | wire_type
        tag_bytes = []
        while True:
            bits = tag & 0x7F
            tag >>= 7
            if tag:
                tag_bytes.append(bits | 0x80)
            else:
                tag_bytes.append(bits)
                break
        return bytes(tag_bytes) + value_bytes

    def _varint_bytes(self, n):
        out = []
        while True:
            bits = n & 0x7F
            n >>= 7
            if n:
                out.append(bits | 0x80)
            else:
                out.append(bits)
                break
        return bytes(out)

    def test_varint_field(self):
        msg = self._make_message(1, 0, self._varint_bytes(42))
        result = _mod._parse_pbf_message(msg)
        self.assertEqual(result[1], 42)

    def test_double_field(self):
        msg = self._make_message(3, 1, struct.pack("<d", 3.14))
        result = _mod._parse_pbf_message(msg)
        self.assertAlmostEqual(result[3], 3.14, places=10)

    def test_bytes_field(self):
        payload = b"hello"
        length_prefix = self._varint_bytes(len(payload))
        msg = self._make_message(2, 2, length_prefix + payload)
        result = _mod._parse_pbf_message(msg)
        self.assertEqual(result[2], b"hello")

    def test_repeated_field_becomes_list(self):
        v1 = self._make_message(1, 0, self._varint_bytes(10))
        v2 = self._make_message(1, 0, self._varint_bytes(20))
        result = _mod._parse_pbf_message(v1 + v2)
        self.assertIsInstance(result[1], list)
        self.assertEqual(result[1], [10, 20])


# ===========================================================================
# PBF geometry decoder
# ===========================================================================


class TestDecodeEsriGeometry(unittest.TestCase):
    """Tests for _decode_esri_geometry using hand-crafted Geometry messages."""

    def _encode_varint(self, n):
        out = []
        while True:
            bits = n & 0x7F
            n >>= 7
            if n:
                out.append(bits | 0x80)
            else:
                out.append(bits)
                break
        return bytes(out)

    def _zigzag_encode(self, n):
        if n >= 0:
            return n << 1
        return ((-n - 1) << 1) | 1

    def _pack_sint64(self, values):
        return b"".join(self._encode_varint(self._zigzag_encode(v)) for v in values)

    def _make_length_field(self, field_num, payload):
        """Build a length-delimited protobuf field."""
        tag = self._encode_varint((field_num << 3) | 2)
        return tag + self._encode_varint(len(payload)) + payload

    def _build_geometry(self, lengths, coords):
        msg = b""
        if lengths:
            msg += self._make_length_field(1, self._pack_sint64(lengths))
        msg += self._make_length_field(2, self._pack_sint64(coords))
        return msg

    def test_point_no_quantization(self):
        # A point at (10.0, 20.0) with no quantization (xy_scale=None)
        # Coordinates stored as delta from (0,0): dx=10, dy=20
        geom = self._build_geometry([], [10, 20])
        result = _mod._decode_esri_geometry(geom, 1, None, 0, 0)
        self.assertEqual(result["type"], "Point")
        self.assertAlmostEqual(result["coordinates"][0], 10.0)
        self.assertAlmostEqual(result["coordinates"][1], 20.0)

    def test_point_with_quantization(self):
        # actual_x = ix / xy_scale + x_origin
        # ix=100000, xy_scale=10000, x_origin=0 → x=10.0
        # iy=200000, xy_scale=10000, y_origin=0 → y=20.0
        geom = self._build_geometry([], [100000, 200000])
        result = _mod._decode_esri_geometry(geom, 1, 10000.0, 0.0, 0.0)
        self.assertEqual(result["type"], "Point")
        self.assertAlmostEqual(result["coordinates"][0], 10.0)
        self.assertAlmostEqual(result["coordinates"][1], 20.0)

    def test_linestring_two_points(self):
        # Two points: (0,0) and (5,5) via deltas [0,0, 5,5]
        geom = self._build_geometry([], [0, 0, 5, 5])
        result = _mod._decode_esri_geometry(geom, 3, None, 0, 0)
        self.assertEqual(result["type"], "LineString")
        self.assertEqual(len(result["coordinates"]), 2)
        self.assertEqual(result["coordinates"][1], [5.0, 5.0])

    def test_multilinestring(self):
        # Two paths of 2 points each; lengths=[2,2]
        # Path 1: (0,0)→(1,1) deltas: [0,0, 1,1]
        # Path 2: continues from (1,1): (3,3)→(4,4) deltas: [2,2, 1,1]
        geom = self._build_geometry([2, 2], [0, 0, 1, 1, 2, 2, 1, 1])
        result = _mod._decode_esri_geometry(geom, 3, None, 0, 0)
        self.assertEqual(result["type"], "MultiLineString")
        self.assertEqual(len(result["coordinates"]), 2)

    def test_polygon_triangle(self):
        # Triangle: (0,0)→(1,0)→(0,1)→close at (0,0)
        # Deltas: [0,0, 1,0, -1,1]; lengths=[3]
        geom = self._build_geometry([3], [0, 0, 1, 0, -1, 1])
        result = _mod._decode_esri_geometry(geom, 4, None, 0, 0)
        self.assertIn(result["type"], ("Polygon", "MultiPolygon"))

    def test_unsupported_geometry_type_returns_none(self):
        geom = self._build_geometry([], [0, 0])
        result = _mod._decode_esri_geometry(geom, 99, None, 0, 0)
        self.assertIsNone(result)


# ===========================================================================
# PBF value decoder
# ===========================================================================


class TestDecodePbfValue(unittest.TestCase):
    def _varint_bytes(self, n):
        out = []
        while True:
            bits = n & 0x7F
            n >>= 7
            if n:
                out.append(bits | 0x80)
            else:
                out.append(bits)
                break
        return bytes(out)

    def _make_field(self, field_num, wire_type, value_bytes):
        tag = self._varint_bytes((field_num << 3) | wire_type)
        return tag + value_bytes

    def _len_delimited(self, field_num, payload):
        return self._make_field(
            field_num, 2, self._varint_bytes(len(payload)) + payload
        )

    def test_string_value(self):
        msg = self._len_delimited(1, "hello".encode())
        self.assertEqual(_mod._decode_pbf_value(msg), "hello")

    def test_double_value(self):
        msg = self._make_field(3, 1, struct.pack("<d", 3.14))
        self.assertAlmostEqual(_mod._decode_pbf_value(msg), 3.14, places=10)

    def test_float_value(self):
        msg = self._make_field(2, 5, struct.pack("<f", 1.5))
        self.assertAlmostEqual(_mod._decode_pbf_value(msg), 1.5, places=5)

    def test_uint32_value(self):
        msg = self._make_field(5, 0, self._varint_bytes(42))
        self.assertEqual(_mod._decode_pbf_value(msg), 42)

    def test_bool_value_true(self):
        msg = self._make_field(9, 0, self._varint_bytes(1))
        self.assertTrue(_mod._decode_pbf_value(msg))

    def test_empty_value_returns_none(self):
        self.assertIsNone(_mod._decode_pbf_value(b""))


# ===========================================================================
# Mocked network – fetch_all_features pagination
# ===========================================================================

_LAYER_INFO = {
    "name": "Test Layer",
    "maxRecordCount": 2,
    "supportedQueryFormats": "JSON,geoJSON,PBF",
    "advancedQueryCapabilities": {"supportsPagination": True},
}

_COUNT_RESP = {"count": 3}

_PAGE_1 = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": None, "properties": {"id": 1}},
        {"type": "Feature", "geometry": None, "properties": {"id": 2}},
    ],
    "exceededTransferLimit": True,
}

_PAGE_2 = {
    "type": "FeatureCollection",
    "features": [
        {"type": "Feature", "geometry": None, "properties": {"id": 3}},
    ],
    "exceededTransferLimit": False,
}


class TestFetchAllFeatures(unittest.TestCase):
    def _side_effects(self, responses):
        it = iter(responses)

        def _effect(url, timeout=120):
            return next(it)

        return _effect

    def test_pagination_collects_all_features(self):
        with patch.object(
            _mod,
            "fetch_json",
            side_effect=self._side_effects([_COUNT_RESP, _PAGE_1, _PAGE_2]),
        ):
            features, fmt = _mod.fetch_all_features(
                "https://host/query", "1=1", "*", "", 2, fmt="geojson"
            )
        self.assertEqual(len(features), 3)
        self.assertEqual([f["properties"]["id"] for f in features], [1, 2, 3])
        self.assertEqual(fmt, "geojson")

    def test_no_features_returns_empty(self):
        with patch.object(_mod, "fetch_json", return_value={"count": 0}):
            features, _ = _mod.fetch_all_features(
                "https://host/query", "1=1", "*", "", 100, fmt="geojson"
            )
        self.assertEqual(features, [])

    def test_pbf_decode_error_falls_back_to_geojson(self):
        """When PBF decoding raises ValueError, module retries with GeoJSON."""

        def _fetch_bytes_bad(url, timeout=120):
            return b"\x00"  # invalid PBF

        responses_json = iter([_COUNT_RESP, _PAGE_1, _PAGE_2])

        def _fetch_json_side(url, timeout=120):
            return next(responses_json)

        with patch.object(
            _mod, "_fetch_raw", side_effect=_fetch_bytes_bad
        ), patch.object(_mod, "fetch_json", side_effect=_fetch_json_side):
            features, fmt = _mod.fetch_all_features(
                "https://host/query", "1=1", "*", "", 2, fmt="pbf"
            )

        # Should have fallen back and still collected all features
        self.assertEqual(fmt, "geojson")
        self.assertEqual(len(features), 3)

    def test_server_error_in_count_raises(self):
        err = {"error": {"code": 400, "message": "Bad request"}}
        with patch.object(_mod, "fetch_json", return_value=err):
            with self.assertRaises(SystemExit):
                _mod.fetch_all_features(
                    "https://host/query", "1=1", "*", "", 100, fmt="geojson"
                )


class TestGetServiceInfo(unittest.TestCase):
    def test_returns_parsed_info(self):
        with patch.object(_mod, "fetch_json", return_value=_LAYER_INFO):
            info = _mod.get_service_info("https://host/layer/0")
        self.assertEqual(info["name"], "Test Layer")

    def test_server_error_raises(self):
        with patch.object(
            _mod, "fetch_json", return_value={"error": {"message": "Forbidden"}}
        ):
            with self.assertRaises(SystemExit):
                _mod.get_service_info("https://host/layer/0")


# ===========================================================================
# fetch_features_page – extra query parameters
# ===========================================================================


class TestFetchFeaturesPageParams(unittest.TestCase):
    """Verify that extra query parameters are encoded into the URL."""

    def _capture_url(self):
        """Return a side-effect that records the URL and returns a dummy page."""
        captured = {}

        def _side(url, timeout=120):
            captured["url"] = url
            return {"features": [], "exceededTransferLimit": False}

        return captured, _side

    def test_geometry_precision_in_url(self):
        captured, side = self._capture_url()
        with patch.object(_mod, "fetch_json", side_effect=side):
            _mod.fetch_features_page(
                "https://h/q",
                "1=1",
                "*",
                "",
                0,
                100,
                fmt="geojson",
                geometry_precision=4,
            )
        self.assertIn("geometryPrecision=4", captured["url"])

    def test_max_offset_in_url(self):
        captured, side = self._capture_url()
        with patch.object(_mod, "fetch_json", side_effect=side):
            _mod.fetch_features_page(
                "https://h/q",
                "1=1",
                "*",
                "",
                0,
                100,
                fmt="geojson",
                max_offset=0.5,
            )
        self.assertIn("maxAllowableOffset=0.5", captured["url"])

    def test_order_by_in_url(self):
        captured, side = self._capture_url()
        with patch.object(_mod, "fetch_json", side_effect=side):
            _mod.fetch_features_page(
                "https://h/q",
                "1=1",
                "*",
                "",
                0,
                100,
                fmt="geojson",
                order_by="NAME ASC",
            )
        self.assertIn("orderByFields=NAME+ASC", captured["url"])

    def test_no_geometry_flag(self):
        captured, side = self._capture_url()
        with patch.object(_mod, "fetch_json", side_effect=side):
            _mod.fetch_features_page(
                "https://h/q",
                "1=1",
                "*",
                "",
                0,
                100,
                fmt="geojson",
                return_geometry=False,
            )
        self.assertIn("returnGeometry=false", captured["url"])

    def test_custom_spatial_rel_in_url(self):
        captured, side = self._capture_url()
        with patch.object(_mod, "fetch_json", side_effect=side):
            _mod.fetch_features_page(
                "https://h/q",
                "1=1",
                "*",
                "-125,42,-116,49",
                0,
                100,
                fmt="geojson",
                spatial_rel="esriSpatialRelContains",
            )
        self.assertIn("esriSpatialRelContains", captured["url"])


# ===========================================================================
# Output formatting – layer list
# ===========================================================================


class TestFormatLayerList(unittest.TestCase):
    ITEMS = [
        {"id": 0, "type": "Feature Layer", "name": "States"},
        {"id": 1, "type": "Table", "name": "Stats"},
    ]

    def test_json_roundtrips(self):
        out = _mod._format_layer_list(self.ITEMS, "json")
        self.assertEqual(json.loads(out), self.ITEMS)

    def test_shell_is_pipe_delimited(self):
        out = _mod._format_layer_list(self.ITEMS, "shell")
        lines = out.splitlines()
        self.assertEqual(lines[0], "0|Feature Layer|States")
        self.assertEqual(lines[1], "1|Table|Stats")

    def test_plain_contains_names_and_header(self):
        out = _mod._format_layer_list(self.ITEMS, "plain")
        self.assertIn("Name", out)
        self.assertIn("States", out)
        self.assertIn("Stats", out)


# ===========================================================================
# Output formatting – layer info
# ===========================================================================


class TestFormatLayerInfo(unittest.TestCase):
    INFO = {
        "id": 0,
        "name": "States",
        "geometry_type": "esriGeometryPolygon",
        "feature_count": 51,
        "max_record_count": 2000,
        "supported_formats": ["JSON", "geoJSON", "PBF"],
        "fields": ["STATE_NAME", "POP2020"],
    }

    def test_json_roundtrips(self):
        out = _mod._format_layer_info(self.INFO, "json")
        self.assertEqual(json.loads(out), self.INFO)

    def test_shell_has_key_value_pairs(self):
        out = _mod._format_layer_info(self.INFO, "shell")
        self.assertIn("name=States", out)
        self.assertIn("feature_count=51", out)
        self.assertIn("fields=STATE_NAME,POP2020", out)

    def test_plain_contains_values(self):
        out = _mod._format_layer_info(self.INFO, "plain")
        self.assertIn("States", out)
        self.assertIn("51", out)
        self.assertIn("STATE_NAME,POP2020", out)

    def test_shell_quotes_names_with_spaces(self):
        info = dict(self.INFO, name="USA States Generalized")
        out = _mod._format_layer_info(info, "shell")
        # The line must be safely sourceable: the space-containing value is quoted.
        self.assertIn("name='USA States Generalized'", out)

    def test_shell_supported_formats_joined(self):
        out = _mod._format_layer_info(self.INFO, "shell")
        self.assertIn("supported_formats=JSON,geoJSON,PBF", out)

    def test_json_feature_count_none_serialises_to_null(self):
        info = dict(self.INFO, feature_count=None)
        data = json.loads(_mod._format_layer_info(info, "json"))
        self.assertIsNone(data["feature_count"])


# ===========================================================================
# list_layers – empty service honours machine-output contract
# ===========================================================================


class TestListLayersEmpty(unittest.TestCase):
    def _run(self, output_format):
        import contextlib
        import io

        buf = io.StringIO()
        with patch.object(
            _mod, "fetch_json", return_value={"layers": [], "tables": []}
        ):
            with contextlib.redirect_stdout(buf):
                _mod.list_layers("https://host/FeatureServer", output_format)
        return buf.getvalue()

    def test_json_empty_prints_empty_array(self):
        self.assertEqual(json.loads(self._run("json")), [])

    def test_shell_empty_prints_no_rows(self):
        self.assertEqual(self._run("shell").strip(), "")

    def test_plain_empty_prints_nothing_to_stdout(self):
        # The human-readable "not found" notice goes to gs.message (stderr).
        self.assertEqual(self._run("plain"), "")


# ===========================================================================
# describe_layer – feature-count failure degrades gracefully
# ===========================================================================


class TestDescribeLayerCountFailure(unittest.TestCase):
    LAYER_INFO = {
        "id": 0,
        "name": "States",
        "geometryType": "esriGeometryPolygon",
        "maxRecordCount": 2000,
        "supportedQueryFormats": "JSON,geoJSON,PBF",
        "fields": [{"name": "STATE_NAME"}],
    }

    def test_count_failure_still_prints_metadata(self):
        import contextlib
        import io

        def _boom(*a, **kw):
            raise SystemExit("query disabled")

        buf = io.StringIO()
        with patch.object(_mod, "get_feature_count", side_effect=_boom):
            with contextlib.redirect_stdout(buf):
                _mod.describe_layer(
                    self.LAYER_INFO,
                    "https://host/q",
                    "1=1",
                    "",
                    output_format="json",
                )
        data = json.loads(buf.getvalue())
        self.assertIsNone(data["feature_count"])
        self.assertEqual(data["name"], "States")
        # supported_formats is normalised to a list (consistent with fields)
        self.assertEqual(data["supported_formats"], ["JSON", "geoJSON", "PBF"])
        self.assertEqual(data["fields"], ["STATE_NAME"])


# ===========================================================================
# Integration tests – real network, real GRASS
# ===========================================================================

_SAMPLE_URL = (
    "https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer/0"
)


def _network_ok():
    import urllib.request

    try:
        urllib.request.urlopen("https://sampleserver6.arcgisonline.com", timeout=5)
        return True
    except Exception:
        return False


@unittest.skipUnless(_network_ok(), "Integration endpoint not reachable")
@unittest.skipUnless("GISBASE" in os.environ, "GRASS GIS environment not active")
class TestIntegration(unittest.TestCase):
    OUTPUT = "test_v_in_ags_cities"

    def test_import_with_where_filter(self):
        import grass.script as gs

        gs.run_command(
            "v.in.ags",
            url=_SAMPLE_URL,
            output=self.OUTPUT,
            where="areaname LIKE 'New%'",
            overwrite=True,
        )
        info = gs.vector_info_topo(self.OUTPUT)
        self.assertGreater(info["points"], 0)

    def test_import_with_spatial_filter(self):
        import grass.script as gs

        gs.run_command(
            "v.in.ags",
            url=_SAMPLE_URL,
            output=self.OUTPUT + "_bbox",
            bbox_filter="-125,42,-116,49",
            overwrite=True,
        )
        info = gs.vector_info_topo(self.OUTPUT + "_bbox")
        self.assertGreater(info["points"], 0)

    @classmethod
    def tearDownClass(cls):
        import grass.script as gs

        gs.run_command(
            "g.remove",
            flags="f",
            type="vector",
            name=",".join([cls.OUTPUT, cls.OUTPUT + "_bbox"]),
            errors="ignore",
        )


if __name__ == "__main__":
    unittest.main()
