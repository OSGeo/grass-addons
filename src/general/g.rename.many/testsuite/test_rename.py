"""g.rename.many tests"""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class ManyRenameTestCase(TestCase):
    """Test wrong input of parameters for g.list module"""

    @classmethod
    def setUpClass(cls):
        """Create maps in a small region."""
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=5, w=0, e=5, res=1)

        # this must be in sync with the csv file
        cls.runModule("r.mapcalc", expression="lidar_259 = 1")
        cls.runModule("r.mapcalc", expression="schools_in_county = 1.0")
        cls.runModule("r.mapcalc", expression="fire = 1.f")
        # including these for the case something fails
        cls.to_remove = ["lidar_259", "schools_in_county", "fire"]

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region and renamed maps (and also old if needed)"""
        cls.runModule("g.remove", name=cls.to_remove, type=["rast"], flags="f")
        cls.del_temp_region()

    def test_raster(self):
        """Test that raster rename works"""
        module = SimpleModule("g.rename.many", raster="data/names.csv")
        self.assertModule(module)
        # this must be in sync with the csv file
        new_names = ["my_special_elevation", "my_special_schools", "my_special_fires"]
        self.to_remove.extend(new_names)
        for name in new_names:
            self.assertRasterExists(name)


if __name__ == "__main__":
    test()
