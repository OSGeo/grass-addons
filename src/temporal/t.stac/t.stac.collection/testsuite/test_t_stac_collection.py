#!/usr/bin/env python3

############################################################################
#
# NAME:      t_stac_collection
#
# AUTHOR:    Corey T. White
#
# PURPOSE:   This is a test file for t.stac.collection
#
# COPYRIGHT: (C) 2023-2024 by Corey T. White and the GRASS Development Team
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
        cls.collection = "naip"
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule("g.region", raster="elevation")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    def test_search_collections(self):
        """Test t.stac.collection without vector metadata creation"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "t.stac.collection", url=self.url, collection_id=self.collection
        )

    def test_collection_id_error(self):
        """Test t.stac.collection with vector metadata creation"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModuleFail("t.stac.collection", url=self.url)

    def test_invalid_collection_id(self):
        """Test t.stac.collection with vector metadata creation"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModuleFail(
            "t.stac.collection", url=self.url, collection_id="naip546"
        )

    # def test_vector_metadata_creation(self):
    #     """Test t.stac.collection with vector metadata creation"""
    #     # assertModule is used to call module which we test
    #     # we expect module to finish successfully
    #     self.assertModule(
    #         "t.stac.collection",
    #         url=self.url,
    #         vector_metadata="test_vector_metadata",
    #         overwrite=True,
    #     )
    #     self.assertVectorExists("test_vector_metadata")


if __name__ == "__main__":
    test()
