import os
import sys
import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.pygrass.utils import get_lib_path
from grass.pygrass.vector.geometry import Point

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


if __name__ == "__main__":
    test()
