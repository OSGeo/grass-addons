from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRGravityTerrain(TestCase):
    input = "test_input"
    output = "test_output"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=10, s=0, e=10, w=0, res=1)
        cls.runModule("r.mapcalc", expression=f"{cls.input} = 1")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="raster", name=cls.input)
        cls.del_temp_region()

    def tearDown(cls):
        """Remove output map after each test method"""
        cls.runModule("g.remove", flags="f", type="raster", name=cls.output)

    def test_output_exists(self):
        """Test output map exists"""
        self.assertModule("r.gravity.terrain", input=self.input, output=self.output)
        self.assertRasterExists(name=self.output, msg="Output was not created")


if __name__ == "__main__":
    test()
