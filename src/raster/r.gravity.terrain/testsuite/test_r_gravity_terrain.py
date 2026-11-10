import os
import csv

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

import grass.script as gs


class TestRGravityTerrain(TestCase):
    elevation = "elevation"
    points = "test_points"
    points3d = "test_points3d"
    output = "test_output.csv"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.elevation)
        gs.write_command(
            "v.in.ascii",
            input="-",
            output=cls.points,
            stdin="637216.750|221422.888\n641376.038|222513.187",
        )
        cls.runModule(
            "v.drape", input=cls.points, output=cls.points3d, elevation=cls.elevation
        )
        cls.runModule("g.region", vector=cls.points, align=cls.elevation, grow=200)

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove", flags="f", type="vector", name=[cls.points, cls.points3d]
        )
        cls.del_temp_region()

    def tearDown(cls):
        """Remove output after each test method"""
        gs.try_remove(cls.output)

    def test_output_exists(self):
        """Test output map exists, just a smoke test"""
        self.assertModule(
            "r.gravity.terrain",
            elevation=self.elevation,
            points=self.points3d,
            minimum_distance=30,
            maximum_distance=2000,
            output=self.output,
            nprocs=1,
        )

        self.assertTrue(os.path.exists(self.output), f"{self.output} does not exist")

        expected_data = {
            1: 0.026039,
            2: 0.016678,
        }

        with open(self.output, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = int(row["category"])
                correction = float(row["correction"])
                self.assertIn(category, expected_data)
                self.assertAlmostEqual(
                    correction,
                    expected_data[category],
                    places=6,
                    msg=f"Correction value for category {category} does not match expected",
                )


if __name__ == "__main__":
    test()
