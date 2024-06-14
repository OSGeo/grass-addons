from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset


class TestEodag(TestCase):
    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.runModule("g.mapset", location="nc_spm_08_grass7", mapset="PERMANENT")
        cls.use_temp_region()

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()

    def test_module_basic_running(self):
        self.assertModule("i.eodag", flags="l")

    def test_sample_one(self):
        cls.runModule(
            "v.extract", input=urbanarea, where="NAME = 'Durham'", output="durham"
        )
        self.assertModule("i.eodag", flags="l", map="durham")

    def test_sample_two(self):
        self.assertModule(
            "i.eodag",
            start="2022-05-25",
            end="2022-06-01",
            dataset="S2_MSI_L2A",
            provider="cop_dataspace",
            clouds=50,
        )

    def test_sample_three(self):
        self.assertModule("i.eodag", file="ids_list.txt", provider="cop_dataspace")

    def test_map_aoi_full_vector_census(self):
        self.assertModule("i.eodag", flags="l", map="census")

    def test_map_aoi_full_vector_census(self):
        self.assertModule("i.eodag", flags="l", map="urbanarea")

    def test_end_comes_first_running(self):
        self.assertModuleFail("i.eodag", start="2020-01-04", end="2020-01-01")


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
