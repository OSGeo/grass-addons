#!/usr/bin/env python3

############################################################################
#
# NAME:      t_stac_catalog
#
# AUTHOR:    Corey T. White
#
# PURPOSE:   This is a test file for t.stac.catalog
#
# COPYRIGHT: (C) 2024 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# Dependencies
# import importlib.util

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule
from pystac_client import Client
import json
from unittest.mock import patch

# spec = importlib.util.spec_from_file_location(
#     name="stac_lib", location="t.stac.collection.py"
# )

# stac_lib = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(stac_lib)


# Tests
class TestStacCatalog(TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        cls.url = "https://earth-search.aws.element84.com/v1/"
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")
        with open("data/catalog.json") as f:
            cls.json_format_expected = json.load(f)

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    # @patch("grass.gunittest.case.TestCase.assertModule")
    @patch("pystac_client.Client.open")
    @patch("pystac_client.Client.get_collections")
    def test_plain_output_json(self, MockClientOpen, MockClientGetCollections):
        """Test t.stac.catalog formated as json"""
        mock_instance = MockClientOpen.return_value
        mock_instance.client = Client.from_dict(self.json_format_expected)
        mock_client_collection = MockClientGetCollections.return_value
        mock_client_collection.get_collections = mock_instance.get_collections()
        self.assertModule("t.stac.catalog", url=self.url, format="json")
        self.assertEqual(mock_instance.outputs.stdout, self.json_format_expected)

    @patch("grass.gunittest.case.TestCase.assertModule")
    def test_plain_output_basic_info_flag(self, MockAssertModule):
        """Testing format as plain basic info"""
        mock_instance = MockAssertModule.return_value
        mock_instance.outputs.stdout = json.dumps(self.json_format_expected)
        self.assertModule("t.stac.catalog", url=self.url, format="plain", flags="b")


if __name__ == "__main__":
    test()
