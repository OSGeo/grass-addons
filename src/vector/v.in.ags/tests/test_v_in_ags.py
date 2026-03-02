"""Tests for v.in.ags

Unit tests exercise the helper functions (URL normalisation, spatial-filter
parameter construction, JSON writing, feature counting) using mocked HTTP
calls so no network connection is required.

Integration tests verify end-to-end behaviour against a real ArcGIS Server.
They are skipped automatically when the network is unavailable.

Run from within a GRASS session:
    python -m pytest tests/test_v_in_ags.py -v

Or with gunittest:
    python -m grass.gunittest.main --config .gunittest.cfg
"""

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Ensure the parent directory is on sys.path so we can import the module
# directly (the GRASS parser is bypassed in unit tests).
# ---------------------------------------------------------------------------
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import helper functions without triggering the GRASS parser.
import importlib
import types

# We load only the helper functions, not main(), to avoid calling gs.parser().
_MODULE_PATH = os.path.join(os.path.dirname(__file__), "..", "v.in.ags.py")


def _load_helpers():
    """Load v.in.ags module helpers without executing main()."""
    spec = importlib.util.spec_from_file_location("v_in_ags", _MODULE_PATH)
    mod = importlib.util.module_from_spec(spec)
    # Provide a stub grass.script so the module-level import succeeds.
    gs_stub = types.ModuleType("grass.script")
    gs_stub.fatal = lambda msg: (_ for _ in ()).throw(SystemExit(msg))
    gs_stub.warning = lambda msg: None
    gs_stub.message = lambda msg: None
    gs_stub.verbose = lambda msg: None
    gs_stub.try_remove = lambda path: None
    gs_stub.overwrite = lambda: False
    gs_stub.vector_history = lambda name: None
    gs_stub.run_command = lambda *a, **kw: None
    sys.modules["grass"] = types.ModuleType("grass")
    sys.modules["grass.script"] = gs_stub
    spec.loader.exec_module(mod)
    return mod


_mod = _load_helpers()

normalize_url = _mod.normalize_url
_apply_extent = _mod._apply_extent
write_geojson = _mod.write_geojson


# ===========================================================================
# Unit tests – no network required
# ===========================================================================


class TestNormalizeUrl(unittest.TestCase):
    """Tests for normalize_url()."""

    def test_url_with_layer_id_unchanged(self):
        url = "https://host/arcgis/rest/services/Svc/FeatureServer/0"
        self.assertEqual(normalize_url(url, 99), url)

    def test_url_with_trailing_slash_stripped(self):
        url = "https://host/arcgis/rest/services/Svc/FeatureServer/0/"
        result = normalize_url(url, 99)
        self.assertEqual(result, url.rstrip("/"))

    def test_url_without_layer_id_appended(self):
        base = "https://host/arcgis/rest/services/Svc/FeatureServer"
        result = normalize_url(base, 3)
        self.assertEqual(result, base + "/3")

    def test_url_layer_id_zero_appended(self):
        base = "https://host/arcgis/rest/services/Svc/FeatureServer"
        result = normalize_url(base, 0)
        self.assertEqual(result, base + "/0")

    def test_url_non_numeric_segment_treated_as_no_layer(self):
        base = "https://host/arcgis/rest/services/Svc/FeatureServer"
        result = normalize_url(base, 7)
        self.assertTrue(result.endswith("/7"))


class TestApplyExtent(unittest.TestCase):
    """Tests for _apply_extent()."""

    def test_empty_extent_no_params_added(self):
        params = {}
        _apply_extent(params, "")
        self.assertEqual(params, {})

    def test_none_extent_no_params_added(self):
        params = {}
        _apply_extent(params, None)
        self.assertEqual(params, {})

    def test_valid_extent_adds_geometry_params(self):
        params = {}
        _apply_extent(params, "-125,42,-116,49")
        self.assertIn("geometry", params)
        self.assertEqual(params["geometryType"], "esriGeometryEnvelope")
        self.assertEqual(params["inSR"], "4326")
        self.assertEqual(params["spatialRel"], "esriSpatialRelIntersects")
        self.assertEqual(params["geometry"], "-125,42,-116,49")

    def test_extent_with_spaces_trimmed(self):
        params = {}
        _apply_extent(params, " -125 , 42 , -116 , 49 ")
        self.assertEqual(params["geometry"], "-125,42,-116,49")

    def test_invalid_extent_raises_fatal(self):
        params = {}
        with self.assertRaises(SystemExit):
            _apply_extent(params, "invalid,extent")


class TestWriteGeoJson(unittest.TestCase):
    """Tests for write_geojson()."""

    def setUp(self):
        self._tmp = tempfile.NamedTemporaryFile(suffix=".geojson", delete=False)
        self._tmp.close()
        self._path = self._tmp.name

    def tearDown(self):
        if os.path.exists(self._path):
            os.unlink(self._path)

    def test_writes_valid_geojson_feature_collection(self):
        features = [
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [-120, 45]},
                "properties": {"name": "Test"},
            }
        ]
        write_geojson(features, self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(len(data["features"]), 1)
        self.assertEqual(data["features"][0]["properties"]["name"], "Test")

    def test_writes_empty_feature_collection(self):
        write_geojson([], self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["type"], "FeatureCollection")
        self.assertEqual(data["features"], [])

    def test_unicode_properties_preserved(self):
        features = [
            {
                "type": "Feature",
                "geometry": None,
                "properties": {"name": "São Paulo"},
            }
        ]
        write_geojson(features, self._path)
        with open(self._path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data["features"][0]["properties"]["name"], "São Paulo")


# ===========================================================================
# Mocked network tests – verify HTTP interaction logic
# ===========================================================================

_LAYER_INFO = {
    "name": "Test Layer",
    "maxRecordCount": 2,
    "advancedQueryCapabilities": {"supportsPagination": True},
    "extent": {"spatialReference": {"wkid": 4326, "latestWkid": 4326}},
}

_COUNT_RESPONSE = {"count": 3}

_PAGE_1 = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-120, 45]},
            "properties": {"id": 1},
        },
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-121, 46]},
            "properties": {"id": 2},
        },
    ],
    "exceededTransferLimit": True,
}

_PAGE_2 = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [-122, 47]},
            "properties": {"id": 3},
        }
    ],
    "exceededTransferLimit": False,
}


class TestFetchAllFeatures(unittest.TestCase):
    """Tests for fetch_all_features() using mocked fetch_json()."""

    def _make_side_effect(self, responses):
        """Return a side-effect function that cycles through *responses*."""
        it = iter(responses)

        def _side_effect(url, timeout=30):
            return next(it)

        return _side_effect

    def test_pagination_collects_all_features(self):
        responses = [_COUNT_RESPONSE, _PAGE_1, _PAGE_2]
        with patch.object(
            _mod, "fetch_json", side_effect=self._make_side_effect(responses)
        ):
            features = _mod.fetch_all_features(
                "https://host/query", "1=1", "*", "", max_record_count=2
            )
        self.assertEqual(len(features), 3)
        ids = [f["properties"]["id"] for f in features]
        self.assertEqual(ids, [1, 2, 3])

    def test_no_features_returns_empty_list(self):
        responses = [{"count": 0}]
        with patch.object(
            _mod, "fetch_json", side_effect=self._make_side_effect(responses)
        ):
            features = _mod.fetch_all_features(
                "https://host/query", "1=1", "*", "", max_record_count=100
            )
        self.assertEqual(features, [])

    def test_server_error_in_count_raises(self):
        err_resp = {"error": {"code": 400, "message": "Invalid query"}}
        with patch.object(_mod, "fetch_json", return_value=err_resp):
            with self.assertRaises(SystemExit):
                _mod.fetch_all_features(
                    "https://host/query", "1=1", "*", "", max_record_count=100
                )


class TestGetServiceInfo(unittest.TestCase):
    """Tests for get_service_info()."""

    def test_returns_parsed_info(self):
        with patch.object(_mod, "fetch_json", return_value=_LAYER_INFO):
            info = _mod.get_service_info("https://host/layer/0")
        self.assertEqual(info["name"], "Test Layer")

    def test_server_error_raises_fatal(self):
        err = {"error": {"code": 403, "message": "Access denied"}}
        with patch.object(_mod, "fetch_json", return_value=err):
            with self.assertRaises(SystemExit):
                _mod.get_service_info("https://host/layer/0")


# ===========================================================================
# Integration tests – require a live ArcGIS Server; skipped if unavailable.
# ===========================================================================

# Public Esri sample FeatureServer used for integration tests.
_SAMPLE_URL = (
    "https://sampleserver6.arcgisonline.com/arcgis/rest/services/USA/MapServer/0"
)


def _network_available():
    """Return True when the integration-test endpoint is reachable."""
    import urllib.request

    try:
        urllib.request.urlopen("https://sampleserver6.arcgisonline.com", timeout=5)
        return True
    except Exception:
        return False


@unittest.skipUnless(_network_available(), "Integration endpoint not reachable")
class TestIntegration(unittest.TestCase):
    """End-to-end tests against a live ArcGIS Server.

    These tests are automatically skipped when the network is unavailable.
    They require a running GRASS session with a WGS84 project.
    """

    OUTPUT = "test_v_in_ags_cities"

    @classmethod
    def setUpClass(cls):
        try:
            from grass.gunittest.case import TestCase as GrassTestCase

            cls._grass_available = True
        except ImportError:
            cls._grass_available = False

    def _run_module(self, **kwargs):
        import grass.script as gs

        return gs.run_command("v.in.ags", **kwargs)

    @unittest.skipUnless("GISBASE" in os.environ, "GRASS GIS environment not active")
    def test_import_with_where_filter(self):
        """Import a small filtered subset from a public service."""
        import grass.script as gs

        self._run_module(
            url=_SAMPLE_URL,
            output=self.OUTPUT,
            where="areaname LIKE 'New%'",
            overwrite=True,
        )
        info = gs.vector_info(self.OUTPUT)
        self.assertGreater(info["primitives"], 0)

    @classmethod
    def tearDownClass(cls):
        if "GISBASE" in os.environ:
            import grass.script as gs

            gs.run_command(
                "g.remove",
                flags="f",
                type="vector",
                name=cls.OUTPUT,
                errors="ignore",
            )


if __name__ == "__main__":
    unittest.main()
