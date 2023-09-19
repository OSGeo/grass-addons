#!/usr/bin/env python3

############################################################################
#
# NAME:      t_stac_import
#
# AUTHOR:    Corey T. White
#
# PURPOSE:   This is a test file for t.stac.import
#
# COPYRIGHT: (C) 2023 by Corey T. White and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# Dependencies
import importlib.util

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from pystac_client import Client

spec = importlib.util.spec_from_file_location(
    name="in_stac_lib", location="t.stac.import.py"
)

in_stac_lib = importlib.util.module_from_spec(spec)
spec.loader.exec_module(in_stac_lib)

# STAC Collections
# Landsat_Collection_2_API_URL = "https://landsatlook.usgs.gov/stac-server/"
# USGS_3DEP_Point_Cloud = "https://stacindex.org/catalogs/usgs-3dep-lidar#/"
# OSC_Catalog = "https://eoepca.github.io/open-science-catalog-metadata/catalog.json"
EARTH_SEARCH_API_URL = "https://earth-search.aws.element84.com/v1/"
# MUNDIALIS_API_URL = "https://openeo.mundialis.de/api/v1.0/"


# Tests
class TestStacImport(TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    @classmethod
    def tearDown(self):
        """
        Remove the outputs created from the centroids module
        This is executed after each test run.
        """
        # self.runModule("g.remove", flags="f", type="raster", name=self.random_walk)
        pass

    def test_search_collections(self):
        """Test t.stac.import"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule("t.stac.import", url=EARTH_SEARCH_API_URL, flags="c")

    def test_search_collection_items(self):
        """Test t.stac.import"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "t.stac.import", url=EARTH_SEARCH_API_URL, collections="naip", flags="i"
        )

    def test_validate_collection(self):
        """
        Tests searching STAC client with no collection set
        """
        client = Client.open(EARTH_SEARCH_API_URL)
        # EARTH_SEARCH_API_URL
        isValid = in_stac_lib.validate_collections_option(client)
        self.assertFalse(isValid)

    def test_import_asset_bbox(self):
        """
        Tests importing STAC asset
        """
        self.assertModule(
            "t.stac.import",
            url=EARTH_SEARCH_API_URL,
            collections=["naip"],
            bbox=[-72.5, 40.5, -72, 41],
            limit=2,
        )

    def test_import_asset_region(self):
        """
        Tests importing STAC asset
        """
        self.assertModule(
            "t.stac.import", url=EARTH_SEARCH_API_URL, collections=["naip"], limit=2
        )


if __name__ == "__main__":
    test()
