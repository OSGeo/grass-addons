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
from grass.gunittest.gmodules import SimpleModule


path = get_lib_path(modname="t.stac", libname="staclib")
if path is None:
    gs.fatal("Not able to find the stac library directory.")
sys.path.append(path)

import staclib as libstac


class TestStaclib(TestCase):
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

    def test_realworld_example(self):
        """Test with a real-world example"""
        stac_query = {"eo:cloud_cover": {"lt": 10}}
        module = SimpleModule(
            "t.stac.item",
            url="https://earth-search.aws.element84.com/v1/",
            collection_id="sentinel-2-l2a",
            datetime="2024-04-01/2024-09-30",
            asset_keys="red,nir",
            query=json.dumps(stac_query),
            format="json",
        )
        self.assertModule(module)


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


if __name__ == "__main__":
    test()
