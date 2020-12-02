"""Test v.stream.order

@author
IGB-Berlin,Johannes Radinger; Implementation: Geoinformatikbuero Dassau GmbH , Soeren Gebbert
This tool was developed as part of the BiodivERsA-net project 'FISHCON'
and has been funded by the German Federal Ministry for Education and
Research (grant number 01LC1205).

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

"""

from grass.gunittest.case import TestCase
from grass.pygrass.vector import VectorTopo


class TestStreamOrder(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.runModule("v.in.ascii", input="data/stream_network.txt",
                      output="stream_network", format="standard",
                      overwrite=True)

        cls.runModule("v.in.ascii", input="data/stream_network_outlets.txt",
                      output="stream_network_outlets", format="standard")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="vector",
                      name="stream_network,stream_network_outlets")

    def tearDown(self):
        pass
        self.runModule("g.remove", flags="f", type="vector",
                       pattern="stream_network_order_test_*")

    def test_strahler(self):
        self.assertModule("v.stream.order", input="stream_network",
                          points="stream_network_outlets",
                          output="stream_network_order_test_strahler",
                          threshold=25,
                          order=["strahler"],
                          overwrite=True, verbose=True)

        # Check the strahler value
        v = VectorTopo(name="stream_network_order_test_strahler",
                       mapset="")
        v.open(mode="r")

        self.assertTrue(v.exist(), True)
        self.assertEqual(v.num_primitive_of("line"), 101)
        # feature 4
        self.assertEqual(v.read(4).attrs.cat, 41)
        self.assertEqual(v.read(4).attrs["outlet_cat"], 1)
        self.assertEqual(v.read(4).attrs["network"], 1)
        self.assertEqual(v.read(4).attrs["reversed"], 0)
        self.assertEqual(v.read(4).attrs["strahler"], 4)

        v.close()

    def test_all(self):
        self.assertModule("v.stream.order", input="stream_network",
                          points="stream_network_outlets",
                          output="stream_network_order_test_all",
                          threshold=25,
                          order=["strahler", "shreve", "drwal", "scheidegger"],
                          overwrite=True, verbose=True)

        # Check all values
        v = VectorTopo(name="stream_network_order_test_all",
                       mapset="")
        v.open(mode="r")
        self.assertTrue(v.exist(), True)
        self.assertEqual(v.num_primitive_of("line"), 101)
        # feature 4
        self.assertEqual(v.read(4).attrs.cat, 41)
        self.assertEqual(v.read(4).attrs["outlet_cat"], 1)
        self.assertEqual(v.read(4).attrs["network"], 1)
        self.assertEqual(v.read(4).attrs["reversed"], 0)
        self.assertEqual(v.read(4).attrs["strahler"], 4)
        self.assertEqual(v.read(4).attrs["shreve"], 32)
        self.assertEqual(v.read(4).attrs["drwal"], 6)
        self.assertEqual(v.read(4).attrs["scheidegger"], 64)
        v.close()

        # Check for column copy
        self.assertModule("v.stream.order",
                          input="stream_network_order_test_all",
                          points="stream_network_outlets",
                          output="stream_network_order_test_all_2",
                          threshold=25,
                          order=["strahler", "shreve", "drwal", "scheidegger"],
                          columns=["strahler", "shreve", "drwal", "scheidegger"],
                          overwrite=True, verbose=True)

        # Check all values and their copies
        v = VectorTopo(name="stream_network_order_test_all_2",
                       mapset="")
        v.open(mode="r")
        self.assertTrue(v.exist(), True)
        self.assertEqual(v.num_primitive_of("line"), 101)
        # feature 4
        self.assertEqual(v.read(4).attrs.cat, 4)
        self.assertEqual(v.read(4).attrs["outlet_cat"], 1)
        self.assertEqual(v.read(4).attrs["network"], 1)
        self.assertEqual(v.read(4).attrs["reversed"], 0)
        self.assertEqual(v.read(4).attrs["strahler"], 4)
        self.assertEqual(v.read(4).attrs["shreve"], 32)
        self.assertEqual(v.read(4).attrs["drwal"], 6)
        self.assertEqual(v.read(4).attrs["scheidegger"], 64)
        self.assertEqual(v.read(4).attrs["strahler_1"], 4)
        self.assertEqual(v.read(4).attrs["shreve_1"], 32)
        self.assertEqual(v.read(4).attrs["drwal_1"], 6)
        self.assertEqual(v.read(4).attrs["scheidegger_1"], 64)
        # feature 7
        self.assertEqual(v.read(7).attrs.cat, 7)
        self.assertEqual(v.read(7).attrs["outlet_cat"], 1)
        self.assertEqual(v.read(7).attrs["network"], 1)
        self.assertEqual(v.read(7).attrs["reversed"], 0)
        self.assertEqual(v.read(7).attrs["strahler"], 2)
        self.assertEqual(v.read(7).attrs["strahler_1"], 2)
        self.assertEqual(v.read(7).attrs["shreve"], 4)
        self.assertEqual(v.read(7).attrs["drwal"], 3)
        self.assertEqual(v.read(7).attrs["scheidegger"], 8)
        v.close()


class TestStreamOrderFails(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.runModule("v.in.ascii", input="data/stream_network.txt",
                      output="stream_network", format="standard",
                      overwrite=True)

        cls.runModule("v.in.ascii", input="data/stream_network_outlets.txt",
                      output="stream_network_outlets", format="standard")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="vector",
                      name="stream_network,stream_network_outlets")

    def test_error_handling_1(self):
        # No input points
        self.assertModuleFail("v.stream.order", input="stream_network",
                              output="stream_network_order", threshold=25,
                              order=["strahler", "shreve", "drwal", "scheidegger"])

    def test_error_handling_2(self):
        # No input network
        self.assertModuleFail("v.stream.order",
                              points="stream_network_outlets",
                              output="stream_network_order", threshold=25,
                              order=["strahler", "shreve", "drwal", "scheidegger"])

    def test_error_handling_3(self):
        # No output
        self.assertModuleFail("v.stream.order", input="stream_network",
                              points="stream_network_outlets",
                              threshold=25,
                              order=["strahler", "shreve", "drwal", "scheidegger"],
                              overwrite=True, verbose=True)

    def test_error_handling_4(self):
        # Recursion limit is below 1000
        self.assertModuleFail("v.stream.order", input="stream_network",
                              points="stream_network_outlets",
                              output="stream_network_order", threshold=25,
                              order=["strahler", "shreve", "drwal", "scheidegger"],
                              recursionlimit=0,
                              overwrite=True, verbose=True)

    def test_error_handling_5(self):
        # Horton order is not implemented
        self.assertModuleFail("v.stream.order", input="stream_network",
                              points="stream_network_outlets",
                              output="stream_network_order", threshold=25,
                              order=["horton"],
                              overwrite=True, verbose=True)

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
