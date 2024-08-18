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

import re
import json
from datetime import datetime
from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset
from grass.exceptions import CalledModuleError
from grass.pygrass.modules import Module
from subprocess import PIPE


class TestEodag(TestCase):

    @classmethod
    def setUpClass(cls):
        """Use temporary region settings."""
        cls.use_temp_region()
        cls.runModule(
            "v.extract",
            input="urbanarea",
            where="NAME = 'Durham'",
            output="durham",
            overwrite=True,
        )
        cls.peps_up = True
        cls.cop_dataspace_up = True
        cls.creodias_up = True
        cls.planetary_computer_up = True
        try:
            cls.runModule(
                "i.eodag",
                flags="l",
                provider="peps",
                producttype="S2_MSI_L1C",
                start="2024-01-01",
                end="2024-01-01",
                map="durham",
                quiet=True,
            )
        except:
            print(
                "Faild to connect to provider 'peps', all testes associated with 'peps' will pass unconditionally."
            )
            cls.peps_up = False
        try:
            cls.runModule(
                "i.eodag",
                flags="l",
                provider="cop_dataspace",
                producttype="S2_MSI_L1C",
                start="2024-01-01",
                end="2024-01-01",
                map="durham",
                quiet=True,
            )
        except:
            print(
                "Faild to connect to provider 'cop_dataspace', all testes associated with 'cop_dataspace' will pass unconditionally."
            )
            cls.cop_dataspace_up = False
        try:
            cls.runModule(
                "i.eodag",
                flags="l",
                provider="creodias",
                producttype="S2_MSI_L1C",
                start="2024-01-01",
                end="2024-01-01",
                map="durham",
                quiet=True,
            )
        except:
            print(
                "Faild to connect to provider 'creodias', all testes associated with 'creodias' will pass unconditionally."
            )
            cls.creodias_up = False
        try:
            cls.runModule(
                "i.eodag",
                flags="l",
                provider="planetary_computer",
                producttype="LANDSAT_C2L2",
                start="2024-01-01",
                end="2024-01-01",
                map="durham",
                quiet=True,
            )
        except:
            print(
                "Faild to connect to provider 'planetary_computer', all testes associated with 'planetary_computer' will pass unconditionally."
            )
            cls.planetary_computer_up = False

    @classmethod
    def tearDownClass(cls):
        """Delete temporary region settings."""
        cls.del_temp_region()

    def test_search_without_date(self):
        """Test search without specifying dates."""
        if not self.__class__.creodias_up:
            return
        self.assertModule(
            "i.eodag",
            flags="l",
            provider="creodias",
            producttype="S2_MSI_L2A",
            clouds=30,
            map="durham",
            quiet=True,
        )

    def test_search_S2_MSI_L2A(self):
        """Test searching for S2_MSI_L2A from creodias."""
        if not self.__class__.creodias_up:
            return
        start_time = datetime.fromisoformat("2024-01-01")
        end_time = datetime.fromisoformat("2024-02-01")
        clouds_limit = 30
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="creodias",
            producttype="S2_MSI_L2A",
            clouds=clouds_limit,
            map="durham",
            start=start_time.isoformat(),
            end=end_time.isoformat(),
            quiet=True,
            stdout_=PIPE,
        )
        for line in i_eodag.outputs["stdout"].value.strip().split("\n"):
            title, sensing_time, clouds, producttype = [
                i.strip() for i in line.split(" ") if i != ""
            ]
            sensing_time = datetime.fromisoformat(sensing_time)
            clouds = int(clouds[:-1])
            self.assertTrue(
                title.startswith("S2A_MSIL2A") or title.startswith("S2B_MSIL2A")
            )
            self.assertTrue(start_time <= sensing_time)
            self.assertTrue(sensing_time <= end_time)
            self.assertTrue(clouds <= 30)
            self.assertTrue(producttype == "S2MSI2A")

    def test_pattern_option(self):
        """Test pattern option using Landsat Collection 2 Level 2,
        checking the ability to get only Tier 1 Landsat 9 scenes."""
        if not self.__class__.planetary_computer_up:
            return
        i_eodag = Module(
            "i.eodag",
            flags="l",
            provider="planetary_computer",
            map="durham",
            producttype="LANDSAT_C2L2",
            pattern="LC09.*T1",
            clouds=30,
            quiet=True,
            stdout_=PIPE,
        )

        pattern = re.compile("LC09.*T1")
        lines = i_eodag.outputs["stdout"].value.strip().split("\n")
        for line in lines:
            scene_id = line.split(" ")[0]
            self.assertTrue(pattern.fullmatch(scene_id))

    def test_query_option(self):
        """Test querying using relativeOrbitNumber"""
        if not self.__class__.peps_up:
            return
        i_eodag = Module(
            "i.eodag",
            flags="j",
            provider="peps",
            producttype="S2_MSI_L1C",
            map="durham",
            start="2024-01-01",
            end="2024-06-01",
            query="relativeOrbitNumber=97",
            limit=10,
            quiet=True,
            stdout_=PIPE,
        )
        result = json.loads(i_eodag.outputs["stdout"].value.strip())
        self.assertTrue("features" in result)
        for scene in result["features"]:
            self.assertTrue("relativeOrbitNumber" in scene["properties"])
            self.assertTrue(scene["properties"]["relativeOrbitNumber"] == 97)

    def test_query_and_pattern(self):
        """Test multi query filtering, while using the pattern option to get only S2B scenes."""
        if not self.__class__.creodias_up:
            return
        i_eodag = Module(
            "i.eodag",
            flags="j",
            provider="creodias",
            producttype="S2_MSI_L1C",
            start="2024-01-01",
            end="2024-06-01",
            order="desc",
            pattern="S2B.*",
            query="relativeOrbitNumber=97,sensorMode=INS-NOBS",
            map="durham",
            limit=20,
            quiet=True,
            stdout_=PIPE,
        )
        result = json.loads(i_eodag.outputs["stdout"].value.strip())
        self.assertTrue("features" in result)
        for scene in result["features"]:
            self.assertTrue("sensorMode" in scene["properties"])
            self.assertTrue("relativeOrbitNumber" in scene["properties"])
            self.assertTrue(scene["properties"]["title"].startswith("S2B"))
            self.assertTrue(scene["properties"]["relativeOrbitNumber"] == 97)
            self.assertTrue(scene["properties"]["sensorMode"] == "INS-NOBS")

    def test_query_multiple_value(self):
        """Testing querying with multiple values covering both the AND and OR relations."""
        if not self.__class__.creodias_up:
            return
        i_eodag = Module(
            "i.eodag",
            flags="j",
            provider="creodias",
            producttype="S2_MSI_L1C",
            start="2024-01-01",
            end="2024-06-01",
            sort="cloudcover",
            order="desc",
            pattern="S2B.*",
            query="relativeOrbitNumber=97|54,sensorMode=INS-NOBS,cloudCover=30;ge,cloudCover=70;le",
            map="durham",
            limit=10,
            quiet=True,
            stdout_=PIPE,
        )
        result = json.loads(i_eodag.outputs["stdout"].value.strip())
        self.assertTrue("features" in result)
        self.assertTrue(len(result["features"]) <= 10)
        for scene in result["features"]:
            self.assertTrue("sensorMode" in scene["properties"])
            self.assertTrue("relativeOrbitNumber" in scene["properties"])
            self.assertTrue(30 <= scene["properties"]["cloudCover"])
            self.assertTrue(scene["properties"]["cloudCover"] <= 70)
            self.assertTrue(scene["properties"]["title"].startswith("S2B"))
            self.assertTrue(
                scene["properties"]["relativeOrbitNumber"] == 97
                or scene["properties"]["relativeOrbitNumber"] == 54
            )
            self.assertTrue(scene["properties"]["sensorMode"] == "INS-NOBS")

    def test_text_file_with_ids(self):
        """Test searching for products from a text file."""
        if not self.__class__.cop_dataspace_up:
            return
        output = r"""S2B_MSIL2A_20240529T081609_N0510_R121_T37SED_20240529T105453 2024-05-29T08:16:09  1% S2MSI2A
S2B_MSIL2A_20240529T081609_N0510_R121_T37TDE_20240529T124818 2024-05-29T08:16:09  6% S2MSI2A"""
        i_eodag = Module(
            "i.eodag",
            flags="l",
            file="data/ids_list.txt",
            provider="cop_dataspace",
            producttype="S2_MSI_L2A",
            sort="cloudcover",
            quiet=True,
            stdout_=PIPE,
        )
        self.assertEqual(i_eodag.outputs["stdout"].value.strip(), output)

    def test_end_comes_first_fail(self):
        """Test"""
        self.assertModuleFail(
            "i.eodag", start="2020-01-04", end="2020-01-01", quiet=True
        )

    def test_minimum_overlap_b(self):
        """Test minimum_overlap and the b flag"""
        # Testing relation could be done with eodag module and refiltering the results
        # but that woule require importing eodag, or alternativley, implementation the relation checker,
        # probably not worth it?
        if not self.__class__.peps_up:
            return
        self.assertModule(
            "i.eodag",
            flags="lb",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-06-01",
            clouds=50,
            map="durham",
            minimum_overlap=70,
            quiet=True,
        )

    def test_area_relation_contains(self):
        """Test area_relation Contains"""
        # Testing relation could be done with eodag module and refiltering the results
        # but that woule require importing eodag, or alternativley, implementation the relation checker,
        # probably not worth it?
        if not self.__class__.peps_up:
            return
        self.assertModule(
            "i.eodag",
            flags="lb",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-07-01",
            clouds=50,
            area_relation="Contains",
            limit=3,
            map="durham",
            quiet=True,
        )

    def test_save_result_geojson(self):
        """Test saving to a geojson."""
        if not self.__class__.peps_up:
            return
        self.assertModule(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-06-01",
            map="durham",
            save="results/search_s2.geojson",
            quiet=True,
            overwrite=True,
        )

    def test_save_footprint(self):
        """Test saving scenes footprints"""
        return
        if not self.__class__.peps_up:
            return
        # TODO: Fix bug
        # The commands runs from the terminal, but fials with:
        # ERROR: Unable to create location from OGR datasource
        # which seems to be produced by v.in.ogr
        # https://github.com/OSGeo/grass-addons/pull/1163/files/978736fa6f881e7fca4997f782db2a65d8372ed0#r1716373067
        self.assertModule(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-06-01",
            map="durham",
            footprints="s2_footprints",
            overwrite=True,
            quiet=True,
        )

    # The tests for the print option can't be strictly tested
    # as the output might change with the change of the EODAG versions
    def test_print_config(self):
        """Test print configuration."""
        self.assertModule(
            "i.eodag",
            print="config",
            quiet=True,
        )

    def test_print_providers(self):
        """Test print recognized providers."""
        self.assertModule(
            "i.eodag",
            print="providers",
            quiet=True,
        )

    def test_print_products(self):
        """Test print recognized products."""
        self.assertModule(
            "i.eodag",
            print="products",
            quiet=True,
        )

    def test_print_specific_product(self):
        """Test print recognized products."""
        self.assertModule(
            "i.eodag",
            print="products",
            producttype="S2_MSI_L2A",
            quiet=True,
        )

    def test_print_products_per_provider(self):
        """Test print products per provider."""
        self.assertModule(
            "i.eodag",
            print="products",
            provider="usgs",
            quiet=True,
        )

    def test_print_queryables(self):
        """Test print queryables of S2_MSI_L2A product."""
        self.assertModule(
            "i.eodag",
            print="queryables",
            provider="cop_dataspace",
            producttype="S2_MSI_L2A",
            quiet=True,
        )


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
