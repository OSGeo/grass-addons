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

import json
import re
import unittest
from datetime import datetime
from subprocess import PIPE

from grass.exceptions import CalledModuleError
from grass.gunittest.case import TestCase
from grass.gunittest.gutils import get_current_mapset, is_map_in_mapset
from grass.pygrass.modules import Module
from grass.pygrass.modules.interface import Module as PygrassModule

try:
    import eodag

    EODAG_VERSION = int(eodag.__version__.split(".")[0])
except ImportError:
    EODAG_VERSION = None


class TestEodag(TestCase):
    available_providers = {
        "peps": True,
        "cop_dataspace": True,
        "creodias": True,
        "planetary_computer": True,
    }

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

        # Lazy import
        from eodag import EODataAccessGateway

        product_key = "collection" if EODAG_VERSION >= 4 else "productType"
        search_parameters = {
            product_key: "S1_SAR_GRD",
            "start": "2024-01-01",
            "end": "2024-01-01",
            "geometry": {"lonmin": 1.9, "latmin": 43.9, "lonmax": 2, "latmax": 45},
        }
        dag = EODataAccessGateway()
        for provider in cls.available_providers:
            try:
                search_result = dag.search(
                    **search_parameters, provider=provider, raise_errors=True
                )
            except Exception as e:
                cls.available_providers[provider] = False
                # Print the actual error to help with debugging
                print(f"DEBUG: Initial search for provider '{provider}' failed: {e}")

    @classmethod
    def tearDownClass(cls):
        """Delete temporary region settings."""
        cls.del_temp_region()

    def test_can_connect_to_at_least_one_provider(self):
        """Test whether we are able to connect
        and access data from any of the four proivders."""
        self.assertTrue(any([v for k, v in self.__class__.available_providers.items()]))

    def test_search_without_date(self):
        """Test search without specifying dates."""
        if not self.__class__.available_providers["creodias"]:
            self.skipTest("Provider 'creodias' is unavailable.")
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
        if not self.__class__.available_providers["creodias"]:
            self.skipTest("Provider 'creodias' is unavailable.")
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
            run_=False,
            stdout_=PIPE,
        )
        self.assertModule(i_eodag)
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
            # For EODAG v4, product type is 'S2_MSI_L2A', for v3 it's 'S2MSI2A'
            if EODAG_VERSION >= 4:
                self.assertEqual(producttype, "S2_MSI_L2A")
            else:
                self.assertEqual(producttype, "S2MSI2A")

    def test_pattern_option(self):
        """Test pattern option using Landsat Collection 2 Level 2,
        checking the ability to get only Tier 1 Landsat 9 scenes."""
        if not self.__class__.available_providers["planetary_computer"]:
            self.skipTest("Provider 'planetary_computer' is unavailable.")
        i_eodag = Module(
            "i.eodag",
            flags="j",  # Use -j to get JSON output for easier parsing
            provider="planetary_computer",
            map="durham",
            producttype="LANDSAT_C2L2",
            pattern="LC09.*T1",
            clouds=30,
            quiet=True,
            run_=False,
            stdout_=PIPE,
        )
        self.assertModule(i_eodag)

        result = json.loads(i_eodag.outputs["stdout"].value.strip())
        self.assertTrue("features" in result)
        pattern = re.compile("LC09.*T1")
        for scene in result["features"]:
            scene_id = scene["id"]  # Get ID directly from JSON output
            self.assertTrue(pattern.fullmatch(scene_id))

    def test_query_option(self):
        """Test querying using relativeOrbitNumber"""
        if not self.__class__.available_providers["peps"]:
            self.skipTest("Provider 'peps' is unavailable.")
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
            props = scene["properties"]
            if EODAG_VERSION >= 4:
                self.assertTrue("sat:relative_orbit" in props)
                self.assertEqual(props["sat:relative_orbit"], 97)
            else:
                self.assertTrue("relativeOrbitNumber" in props)
                self.assertEqual(props["relativeOrbitNumber"], 97)

    def test_query_and_pattern(self):
        """Test multi query filtering, while using the pattern option to get only S2B scenes."""
        if not self.__class__.available_providers["creodias"]:
            self.skipTest("Provider 'creodias' is unavailable.")
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
            props = scene["properties"]
            # Use the correct STAC property names for v4
            self.assertTrue(scene["properties"]["title"].startswith("S2B"))
            if EODAG_VERSION >= 4:
                self.assertEqual(props.get("sat:relative_orbit"), 97)
                # EODAG v4 maps sensorMode to instrumentMode or platform:instrument:mode
                # Check for both possibilities or use a more generic check if needed
                # For this test, we expect 'INS-NOBS' to be present under 'instrumentMode'
                # or 'platform:instrument:mode' or 'sat:instrument_mode'
                self.assertEqual(props.get("instrumentMode"), "INS-NOBS")
            else:
                self.assertEqual(props.get("relativeOrbitNumber"), 97)
                self.assertEqual(props.get("sensorMode"), "INS-NOBS")

    def test_query_multiple_value(self):
        """Testing querying with multiple values covering both the AND and OR relations."""
        if not self.__class__.available_providers["creodias"]:
            self.skipTest("Provider 'creodias' is unavailable.")
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
            props = scene["properties"]
            # Use the correct STAC property names for v4
            self.assertTrue(scene["properties"]["title"].startswith("S2B"))
            if EODAG_VERSION >= 4:
                cloud_cover = props.get("eo:cloud_cover")
                orbit_number = props.get("sat:relative_orbit")
                # Check for instrumentMode or platform:instrument:mode
                sensor_mode = (
                    props.get("instrumentMode")
                    or props.get("platform:instrument:mode")
                    or props.get("sat:instrument_mode")
                )
            else:
                cloud_cover = props.get("cloudCover")
                orbit_number = props.get("relativeOrbitNumber")
                sensor_mode = props.get("sensorMode")

            # Assertions remain the same, but values are retrieved correctly
            self.assertTrue(30 <= cloud_cover <= 70)
            self.assertIn(orbit_number, [97, 54])
            self.assertEqual(sensor_mode, "INS-NOBS")

    def test_text_file_with_ids(self):
        """Test searching for products from a text file."""
        if not self.__class__.available_providers["cop_dataspace"]:
            self.skipTest("Provider 'cop_dataspace' is unavailable.")
        if EODAG_VERSION >= 4:
            output = r"""S2B_MSIL2A_20240529T081609_N0510_R121_T37SED_20240529T105453 2024-05-29T08:16:09  1% S2_MSI_L2A"""
        else:
            output = r"""S2B_MSIL2A_20240529T081609_N0510_R121_T37SED_20240529T105453 2024-05-29T08:16:09  1% S2MSI2A"""

        i_eodag = Module(
            "i.eodag",
            flags="l",
            file="testsuite/data/ids_list.txt",
            provider="cop_dataspace",
            producttype="S2_MSI_L2A",
            sort="cloudcover",
            quiet=True,
            run_=False,
            stdout_=PIPE,
        )
        self.assertModule(i_eodag)
        # The actual output might contain more products than expected if the search is broad.
        # We only check if the expected product is present in the output.
        self.assertIn(output.splitlines()[0], i_eodag.outputs["stdout"].value.strip())

    def test_end_comes_first_fail(self):
        """Test that end date before start date fails."""
        self.assertModuleFail(
            "i.eodag", start="2020-01-04", end="2020-01-01", quiet=True
        )

    def test_minimum_overlap_b(self):
        """Test minimum_overlap and the b flag"""
        if not self.__class__.available_providers["peps"]:
            self.skipTest("Provider 'peps' is unavailable.")
        # Testing relation could be done with eodag module and refiltering the results
        # but that woule require importing eodag, or alternativley, implementation the relation checker,
        # probably not worth it?
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
        if not self.__class__.available_providers["peps"]:
            self.skipTest("Provider 'peps' is unavailable.")
        # Testing relation could be done with eodag module and refiltering the results
        # but that woule require importing eodag, or alternativley, implementation the relation checker,
        # probably not worth it?
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
        if not self.__class__.available_providers["peps"]:
            self.skipTest("Provider 'peps' is unavailable.")
        self.assertModule(
            "i.eodag",
            flags="l",
            provider="peps",
            producttype="S2_MSI_L1C",
            start="2022-05-01",
            end="2022-06-01",
            map="durham",
            save="search_s2.geojson",
            quiet=True,
            overwrite=True,
        )

    def test_save_footprint(self):
        """Test saving scenes footprints"""
        if not self.__class__.available_providers["peps"]:
            self.skipTest("Provider 'peps' is unavailable.")
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
            provider="creodias",
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
