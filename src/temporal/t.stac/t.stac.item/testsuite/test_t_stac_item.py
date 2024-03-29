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
# import importlib.util

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


# Tests
class TestStacItem(TestCase):
    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        cls.url = "https://earth-search.aws.element84.com/v1/"
        cls.collections = "naip"

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        pass

    def test_search_collections(self):
        """Test t.stac.collection without vector metadata creation"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule("t.stac.item", url=self.url, collections=self.collections)

    def test_collections_not_found(self):
        """Test t.stac.collection with vector metadata creation"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule("t.stac.item", url=self.url, collections="naip546")


if __name__ == "__main__":
    test()
