############################################################################
#
# MODULE:      i.eodag
#
# AUTHOR(S):   Hamed Elgizery <hamedashraf2004 gmail.com>
# MENTOR(S):   Luca Delucchi, Veronica Andreo, Stefan Blumentrath
#
# PURPOSE:     Tests i.eodag input parsing / searching results.
#              Uses NC Full data set.
#
# COPYRIGHT:   (C) 2024-2025 by Hamed Elgizery, and the GRASS development team
#
#              This program is free software under the GNU General Public
#              License (>=v2). Read the file COPYING that comes with GRASS
#              for details.
#
#############################################################################

from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset
from grass.exceptions import CalledModuleError


class TestEodag(TestCase):
    @classmethod
    def setUpClass(cls):
        """Use temporary region settings"""
        cls.runModule("g.mapset", location="nc_spm_08_grass7", mapset="PERMANENT")
        cls.use_temp_region()

    @classmethod
    def tearDownClass(cls):
        """Delete temporary region settings"""
        cls.del_temp_region()

    def test_module_basic_running(self):
        """Test"""
        self.assertModule("i.eodag", flags="l")

    def test_sample_one(self):
        """Test"""
        # Extract vector if not already extracted
        try:
            self.runModule(
                "v.extract", input="urbanarea", where="NAME = 'Durham'", output="durham"
            )
        except CalledModuleError:
            pass
        self.assertModule("i.eodag", flags="l", map="durham")

    def test_sample_two(self):
        """Test"""
        self.assertModule(
            "i.eodag",
            flags="l",
            start="2022-05-25",
            end="2022-06-01",
            dataset="S2_MSI_L2A",
            provider="cop_dataspace",
            clouds=50,
        )
        # TODO: Once there is a way to save the results / parse them
        #       check that cloudCover of all of them <= 50

    def test_sample_three(self):
        """Test"""
        self.assertModule(
            "i.eodag", flags="l", file="data/ids_list.txt", provider="cop_dataspace"
        )

    def test_map_aoi_full_vector_census(self):
        """Test"""
        self.assertModule("i.eodag", flags="l", map="census_wake2000")

    def test_map_aoi_full_vector_census(self):
        """Test"""
        self.assertModule("i.eodag", flags="l", map="urbanarea")

    def test_end_comes_first_fail(self):
        """Test"""
        self.assertModuleFail("i.eodag", start="2020-01-04", end="2020-01-01")


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
