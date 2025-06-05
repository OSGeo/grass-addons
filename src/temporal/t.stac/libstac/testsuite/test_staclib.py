#!/usr/bin/env python3

import io
import sys
import json
import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.pygrass.utils import get_lib_path
from grass.pygrass.vector.geometry import Point
from unittest.mock import patch, MagicMock
import base64
import tempfile

path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)

import staclib as libstac


class TestStaclib(TestCase):
    """libstac tests"""

    def test_wgs84_bbox_to_boundary(self):
        """Test wgs84_bbox_to_boundary"""
        input_bbox = [-122.5, 37.5, -122, 38]
        expected_output = {
            "west": "-3117391.51",
            "south": "1246003.91",
            "east": "-3053969.74",
            "north": "1277745.33",
        }

        output = libstac.wgs84_bbox_to_boundary(bbox=input_bbox)
        self.assertEqual(output, expected_output)

    def test_safe_float_cast(self):
        input = {
            "west": "-3117391.51",
            "south": "1246003.91",
            "east": "-3053969.74",
            "north": "1277745.33",
        }
        expected_output = [-3117391.51, 1246003.91, -3053969.74, 1277745.33]
        values = [libstac.safe_float_cast(i) for i in input.values()]
        self.assertEqual(values, expected_output)

    def test_safe_float_cast_fail(self):
        input = {"west": "*", "south": "1246003.91", "east": "*", "north": "1277745.33"}
        expected_output = False
        # Check if all values are float and return False if not
        values = all([libstac.safe_float_cast(i) for i in input.values()])
        self.assertEqual(values, expected_output)

    def test_bbox_to_nodes(self):
        """Test that Python can count to two"""
        input_bbox = {
            "west": -3117391.51,
            "south": 1246003.91,
            "east": -3053969.74,
            "north": 1277745.33,
        }

        # Format of the output
        # [(w, s), (w, n), (e, n), (e, s), (w, s)]
        expected_output = [
            Point(input_bbox["west"], input_bbox["south"]),
            Point(input_bbox["west"], input_bbox["north"]),
            Point(input_bbox["east"], input_bbox["north"]),
            Point(input_bbox["east"], input_bbox["south"]),
            Point(input_bbox["west"], input_bbox["south"]),
        ]

        output = libstac.bbox_to_nodes(bbox=input_bbox)
        self.assertEqual(output, expected_output)

    def test_polygon_centroid(self):
        input_polygon = [
            Point(-3117391.51, 1246003.91),
            Point(-3117391.51, 1277745.33),
            Point(-3053969.74, 1277745.33),
            Point(-3053969.74, 1246003.91),
            Point(-3117391.51, 1246003.91),
        ]

        expected_output = Point(-3085680.625, 1261874.62)
        output = libstac.polygon_centroid(input_polygon)
        self.assertEqual(output, expected_output)

    def test_create_metadata_vector(self):
        mock_metadata = [
            {
                "id": "test",
                "title": "Test",
                "description": "Test description",
                "type": "collection",
                "extent": {
                    "spatial": {
                        "bbox": [[-122.5, 37.5, -122, 38]],
                    },
                    "temporal": {
                        "interval": [["2021-01-01T00:00:00Z", "2021-01-31T23:59:59Z"]]
                    },
                },
                "license": "proprietary",
                "stac_version": "1.0.0",
                "keywords": ["test", "testing"],
            },
            {
                "id": "test2",
                "title": "Test 2",
                "description": "Test description 2",
                "type": "collection",
                "extent": {
                    "spatial": {
                        "bbox": [[-122.5, 37.5, -122, 38]],
                    },
                    "temporal": {
                        "interval": [["2021-01-01T00:00:00Z", "2021-01-31T23:59:59Z"]]
                    },
                },
                "license": "proprietary",
                "stac_version": "1.0.0",
                "keywords": ["test", "testing"],
            },
        ]

        libstac.create_metadata_vector(vector="test", metadata=mock_metadata)
        pass


class TestPrintJsonToStdout(TestCase):
    def setUp(self):
        # Redirect stdout to capture output for testing
        self.stdout = io.StringIO()
        self.original_stdout = sys.stdout
        sys.stdout = self.stdout

    def tearDown(self):
        # Restore original stdout
        sys.stdout = self.original_stdout

    def test_print_json_dict_pretty(self):
        """Test pretty-printing a dictionary"""
        data = {"key": "value", "number": 42}
        expected_output = json.dumps(data, indent=4) + "\n"
        result = libstac.print_json_to_stdout(data, pretty=True)
        self.assertEqual(self.stdout.getvalue(), expected_output)
        self.assertEqual(result, expected_output.strip())

    def test_print_json_dict_compact(self):
        """Test compact printing of a dictionary"""
        data = {"key": "value", "number": 42}
        expected_output = json.dumps(data) + "\n"
        result = libstac.print_json_to_stdout(data, pretty=False)
        self.assertEqual(self.stdout.getvalue(), expected_output)
        self.assertEqual(result, expected_output.strip())

    def test_print_json_list_pretty(self):
        """Test pretty-printing a list"""
        data = [{"key": "value"}, {"number": 42}]
        expected_output = json.dumps(data, indent=4) + "\n"
        result = libstac.print_json_to_stdout(data, pretty=True)
        self.assertEqual(self.stdout.getvalue(), expected_output)
        self.assertEqual(result, expected_output.strip())

    def test_print_json_list_compact(self):
        """Test compact printing of a list"""
        data = [{"key": "value"}, {"number": 42}]
        expected_output = json.dumps(data) + "\n"
        result = libstac.print_json_to_stdout(data, pretty=False)
        self.assertEqual(self.stdout.getvalue(), expected_output)
        self.assertEqual(result, expected_output.strip())

    @patch("grass.script.fatal")
    def test_print_json_invalid_data(self, mock_fatal):
        """Test handling of invalid JSON data"""
        data = {"key": set([1, 2, 3])}  # Sets are not JSON-serializable
        libstac.print_json_to_stdout(data, pretty=False)
        mock_fatal.assert_called_once_with(
            "Failed to serialize data to JSON: Object of type set is not JSON serializable"
        )


class TestEstimateDownloadSize(TestCase):
    @patch("requests.head")
    def test_estimate_download_size_with_metadata_size(self, mock_head):
        """Test estimate_download_size when size is available in metadata."""
        assets = [
            {"href": "http://example.com/asset1", "file:size": 1024},
            {"href": "http://example.com/asset2", "file:size": 2048},
        ]
        expected_output = {"count": 2, "bytes": 3072}

        output = libstac.estimate_download_size(assets)
        self.assertEqual(output, expected_output)
        mock_head.assert_not_called()

    @patch("requests.head")
    def test_estimate_download_size_with_head_request(self, mock_head):
        """Test estimate_download_size when size is fetched using HEAD request."""
        mock_head.return_value = MagicMock(
            status_code=200, headers={"Content-Length": "4096"}
        )
        assets = [
            {"href": "http://example.com/asset1"},
            {"href": "http://example.com/asset2"},
        ]
        expected_output = {"count": 2, "bytes": 8192}

        output = libstac.estimate_download_size(assets)
        self.assertEqual(output, expected_output)
        self.assertEqual(mock_head.call_count, 2)

    @patch("requests.head")
    def test_estimate_download_size_with_mixed_assets(self, mock_head):
        """Test estimate_download_size with a mix of metadata size and HEAD request."""
        mock_head.return_value = MagicMock(
            status_code=200, headers={"Content-Length": "4096"}
        )
        assets = [
            {"href": "http://example.com/asset1", "file:size": 1024},
            {"href": "http://example.com/asset2"},
        ]
        expected_output = {"count": 2, "bytes": 5120}

        output = libstac.estimate_download_size(assets)
        self.assertEqual(output, expected_output)
        self.assertEqual(mock_head.call_count, 1)

    @patch("requests.head")
    def test_estimate_download_size_with_failed_head_request(self, mock_head):
        """Test estimate_download_size when HEAD request fails."""
        mock_head.return_value = MagicMock(status_code=404)
        assets = [{"href": "http://example.com/asset1"}]
        expected_output = {"count": 1, "bytes": 0}

        output = libstac.estimate_download_size(assets)
        self.assertEqual(output, expected_output)
        mock_head.assert_called_once()

    @patch("requests.head")
    def test_estimate_download_size_with_import_error(self, mock_head):
        """Test estimate_download_size when requests module is not available."""
        with patch("staclib.gs.warning") as mock_warning:
            with patch(
                "requests.head", side_effect=ImportError("No module named requests")
            ):
                assets = [{"href": "http://example.com/asset1"}]
                expected_output = {"count": 1, "bytes": 0}

                output = libstac.estimate_download_size(assets)
                self.assertEqual(output, expected_output)
                mock_warning.assert_called_once_with(
                    "requests module not available: No module named requests"
                )

    @patch("requests.head")
    def test_estimate_download_size_with_exception(self, mock_head):
        """Test estimate_download_size when an exception occurs during HEAD request."""
        mock_head.side_effect = Exception("Unexpected error")
        with patch("staclib.gs.warning") as mock_warning:
            assets = [{"href": "http://example.com/asset1"}]
            expected_output = {"count": 1, "bytes": 0}

            output = libstac.estimate_download_size(assets)
            self.assertEqual(output, expected_output)
            mock_warning.assert_called_once_with(
                "Error fetching size for asset http://example.com/asset1: Unexpected error"
            )


class TestEncodeCredentials(TestCase):
    def test_encode_credentials_basic(self):
        username = "user"
        password = "pass"
        expected = base64.b64encode(b"user:pass").decode("utf-8")
        result = libstac.encode_credentials(username, password)
        self.assertEqual(result, expected)

    def test_encode_credentials_empty_username(self):
        username = ""
        password = "pass"
        expected = base64.b64encode(b":pass").decode("utf-8")
        result = libstac.encode_credentials(username, password)
        self.assertEqual(result, expected)

    def test_encode_credentials_empty_password(self):
        username = "user"
        password = ""
        expected = base64.b64encode(b"user:").decode("utf-8")
        result = libstac.encode_credentials(username, password)
        self.assertEqual(result, expected)

    def test_encode_credentials_both_empty(self):
        username = ""
        password = ""
        expected = base64.b64encode(b":").decode("utf-8")
        result = libstac.encode_credentials(username, password)
        self.assertEqual(result, expected)

    def test_encode_credentials_special_characters(self):
        username = "usér"
        password = "päss:with:colons"
        expected = base64.b64encode("usér:päss:with:colons".encode("utf-8")).decode(
            "utf-8"
        )
        result = libstac.encode_credentials(username, password)
        self.assertEqual(result, expected)


class TestSetRequestHeaders(TestCase):
    """Test set_request_headers function"""

    @patch("staclib.encode_credentials", return_value="encoded")
    def test_set_request_headers_from_file(self, mock_encode):
        # Create a temporary file with username and password
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("user\npass\n")
            tmp.flush()
            tmp_name = tmp.name

        expected = {"Authorization": "Basic encoded"}
        result = libstac.set_request_headers(tmp_name)
        self.assertEqual(result, expected)
        mock_encode.assert_called_once_with("user", "pass")

    @patch("staclib.encode_credentials", return_value="encoded")
    def test_set_request_headers_from_file_with_blank_lines(self, mock_encode):
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("\nuser\npass\n\n")
            tmp.flush()
            tmp_name = tmp.name

        expected = {"Authorization": "Basic encoded"}
        result = libstac.set_request_headers(tmp_name)
        self.assertEqual(result, expected)
        mock_encode.assert_called_once_with("user", "pass")

    @patch("grass.script.fatal")
    def test_set_request_headers_file_too_short(self, mock_fatal):
        mock_fatal.side_effect = SystemExit  # Simulate fatal error raising SystemExit
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("user\n")
            tmp.flush()
            tmp_name = tmp.name

        with self.assertRaises(SystemExit):
            libstac.set_request_headers(tmp_name)
        mock_fatal.assert_called_once_with("Invalid settings file")

    @patch("grass.script.fatal")
    def test_set_request_headers_file_oserror(self, mock_fatal):
        mock_fatal.side_effect = SystemExit  # Simulate fatal error raising SystemExit

        with self.assertRaises(SystemExit):
            libstac.set_request_headers("/nonexistent/file/path")
        self.assertTrue(
            mock_fatal.call_args[0][0].startswith("Unable to open settings file:")
        )

    @patch("staclib.encode_credentials", return_value="encoded")
    @patch("builtins.input", return_value="user")
    @patch("getpass.getpass", return_value="pass")
    def test_set_request_headers_stdin(self, mock_getpass, mock_input, mock_encode):
        expected = {"Authorization": "Basic encoded"}
        result = libstac.set_request_headers("-")
        self.assertEqual(result, expected)
        mock_input.assert_called_once()
        mock_getpass.assert_called_once()
        mock_encode.assert_called_once_with("user", "pass")

    def test_set_request_headers_empty_settings(self):
        # Should return empty dict if settings is falsy
        result = libstac.set_request_headers("")
        self.assertEqual(result, {})

    @patch("grass.script.fatal")
    def test_set_request_headers_no_user_or_password(self, mock_fatal):
        mock_fatal.side_effect = SystemExit  # Simulate fatal error raising SystemExit
        # Simulate file with blank lines only
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("\n\n")
            tmp.flush()
            tmp_name = tmp.name

        with self.assertRaises(SystemExit):
            libstac.set_request_headers(tmp_name)
        mock_fatal.assert_called_once_with("Invalid settings file")

    @patch("grass.script.fatal")
    def test_set_request_headers_none_user_or_password(self, mock_fatal):
        mock_fatal.side_effect = SystemExit  # Simulate fatal error raising SystemExit
        # Simulate file with two blank lines (should trigger "No user or password given")
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("\n\n\n")
            tmp.flush()
            tmp_name = tmp.name

        with self.assertRaises(SystemExit):
            # This will fail at the "Invalid settings file" check, not "No user or password given"
            libstac.set_request_headers(tmp_name)
        mock_fatal.assert_called_once_with("Invalid settings file")


class TestReadJsonToDict(TestCase):
    def test_read_json_to_dict_valid_file(self):
        # Create a temporary JSON file with valid content
        data = {"foo": "bar", "num": 42}
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            json.dump(data, tmp)
            tmp.flush()
            tmp_name = tmp.name

        result = libstac.read_json_to_dict(tmp_name)
        self.assertEqual(result, data)

    def test_read_json_to_dict_empty_file(self):
        # Create an empty temporary file
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp_name = tmp.name

            result = libstac.read_json_to_dict(tmp_name)
            self.assertEqual(result, {})

    def test_read_json_to_dict_nonexistent_file(self):
        # Use a file path that does not exist
        result = libstac.read_json_to_dict("/nonexistent/path/to/file.json")
        self.assertEqual(result, {})

    def test_read_json_to_dict_invalid_json(self):
        # Create a file with invalid JSON
        with tempfile.NamedTemporaryFile(mode="w+", delete=False) as tmp:
            tmp.write("{invalid json}")
            tmp.flush()
            tmp_name = tmp.name

        result = libstac.read_json_to_dict(tmp_name)
        self.assertEqual(result, {})

    class TestWgs84GeojsonFromVector(TestCase):
        def setUp(self):
            self.helper = libstac.STACHelper()

        @patch.object(libstac.STACHelper, "_renderer")
        @patch("staclib.read_json_to_dict")
        def test_wgs84_geojson_from_vector_success(self, mock_read_json, mock_renderer):
            # Simulate renderer returns a file path, and read_json_to_dict returns a dict
            mock_renderer.render_vector.return_value = "/tmp/vector.geojson"
            mock_read_json.return_value = {"type": "FeatureCollection", "features": []}
            result = self.helper.wgs84_geojson_from_vector("test_vector")
            mock_renderer.render_vector.assert_called_once_with("test_vector")
            mock_read_json.assert_called_once_with("/tmp/vector.geojson")
            self.assertEqual(result, {"type": "FeatureCollection", "features": []})

        @patch.object(libstac.STACHelper, "_renderer")
        @patch("staclib.read_json_to_dict")
        def test_wgs84_geojson_from_vector_none_vector_name(
            self, mock_read_json, mock_renderer
        ):
            # If vector_name is None or empty, should return None and not call renderer
            result = self.helper.wgs84_geojson_from_vector("")
            mock_renderer.render_vector.assert_not_called()
            mock_read_json.assert_not_called()
            self.assertIsNone(result)

        @patch.object(libstac.STACHelper, "_renderer")
        @patch("grass.script.fatal")
        def test_wgs84_geojson_from_vector_raises_exception(
            self, mock_fatal, mock_renderer
        ):
            # Simulate renderer raising an exception
            mock_renderer.render_vector.side_effect = Exception("fail")
            mock_fatal.side_effect = SystemExit  # Simulate gs.fatal exiting
            with self.assertRaises(SystemExit):
                self.helper.wgs84_geojson_from_vector("test_vector")
            mock_renderer.render_vector.assert_called_once_with("test_vector")
            mock_fatal.assert_called_once()


if __name__ == "__main__":
    test()
