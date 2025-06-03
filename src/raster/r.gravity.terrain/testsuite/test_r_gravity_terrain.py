import os

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

import grass.script as gs


class TestRGravityTerrain(TestCase):
    elevation = "test_elevation"
    points = "test_points"
    output = "test_output.csv"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=0, e=5, w=0, res=1)
        gs.write_command(
            "v.in.ascii", input="-", output=cls.points, z=3, stdin="2.5|2.5|1"
        )
        cls.runModule("r.mapcalc", expression=f"{cls.elevation} = 1")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="raster", name=cls.elevation)
        cls.runModule("g.remove", flags="f", type="vector", name=cls.points)
        cls.del_temp_region()

    def tearDown(cls):
        """Remove output after each test method"""
        gs.try_remove(cls.output)

    def test_output_exists(self):
        """Test output map exists, just a smoke test"""
        self.assertModule(
            "r.gravity.terrain",
            elevation=self.elevation,
            points=self.points,
            minimum_distance=1,
            maximum_distance=5,
            output=self.output,
        )
        self.assertTrue(os.path.exists(self.output), f"{self.output} does not exist")


if __name__ == "__main__":
    test()
