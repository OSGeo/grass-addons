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

# spec = importlib.util.spec_from_file_location(
#     name="stac_lib", location="t.stac.collection.py"
# )

# stac_lib = importlib.util.module_from_spec(spec)
# spec.loader.exec_module(stac_lib)


# Tests
class TestStacCollection(TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        cls.url = "https://earth-search.aws.element84.com/v1/"
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    def test_stac_catalog(self):
        """Test t.stac.catalog"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule("t.stac.catalog", url=self.url)

    def test_stac_catalog_basic_info(self):
        """Test t.stac.catalog with basic info"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule("t.stac.catalog", url=self.url, b=True)


if __name__ == "__main__":
    test()
