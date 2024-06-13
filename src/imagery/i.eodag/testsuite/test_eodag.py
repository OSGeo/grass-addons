from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset


class TestEodag(TestCase):
    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.runModule("g.mapset", location="nc_basic_spm_grass7", mapset="PERMANENT")
        cls.use_temp_region()

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()

    def test_module_basic(self):
        self.assertModule("i.eodag", flags="l")

    def test_map_aoi(self):
        self.assertModule("i.eodag", flags="l", map="census")

    def test_end_comes_first(self):
        self.assertModuleFail("i.eodag", start="2020-01-04", end="2020-01-01")


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
