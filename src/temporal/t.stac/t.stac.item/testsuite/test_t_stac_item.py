# #!/usr/bin/env python3

# ############################################################################
# #
# # NAME:      t_stac_item
# #
# # AUTHOR:    Corey T. White
# #
# # PURPOSE:   This is a test file for t.stac.item
# #
# # COPYRIGHT: (C) 2023 by Corey T. White and the GRASS Development Team
# #
# #            This program is free software under the GNU General Public
# #            License (>=v2). Read the file COPYING that comes with GRASS
# #            for details.
# #
# #############################################################################

# # Dependencies
# # import importlib.util

# from grass.gunittest.case import TestCase
# from grass.gunittest.main import test


# # Tests
# class TestStacItem(TestCase):
#     @classmethod
#     def setUpClass(cls):
#         """Ensures expected computational region"""
#         cls.url = "https://earth-search.aws.element84.com/v1/"
#         cls.collections = "naip"

#     @classmethod
#     def tearDownClass(cls):
#         """Remove temporary region"""
#         pass

#     def test_search_items(self):
#         """Test t.stac.item without vector metadata creation"""
#         # Should return count of items found in the collection
#         self.assertModule("t.stac.item", url=self.url, collections=self.collections)

#     def test_search_items_summary_json(self):
#         """Test t.stac.item with JSON output"""
#         # Should return JSON output of items found in the collection
#         self.assertModule(
#             "t.stac.item",
#             url=self.url,
#             collections=self.collections,
#             format="json",
#             flag="m",
#         )

#     def test_search_items_summary_plain(self):
#         """Test t.stac.item with plain text output"""
#         # Should return plain text output of items found in the collection
#         self.assertModule(
#             "t.stac.item",
#             url=self.url,
#             collections=self.collections,
#             format="plain",
#             flag="m",
#         )

#     def test_search_items_vector_footprint(self):
#         """Test t.stac.item with vector metadata creation"""
#         # Should return vector metadata of items found in the collection
#         self.assertModule(
#             "t.stac.item",
#             url=self.url,
#             collections=self.collections,
#             vector="naip_footprints",
#             flag="m",
#         )

#     def test_collections_not_found(self):
#         """Test t.stac.collection with vector metadata creation"""
#         # assertModule is used to call module which we test
#         # we expect module to finish successfully
#         self.assertModule("t.stac.item", url=self.url, collections="naip546")


# if __name__ == "__main__":
#     test()
