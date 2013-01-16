
import unittest2 as unittest
#import unittest

from libagent import playground, grassland

class TestOurExceptions(unittest.TestCase):
    def setUp(self):              
        self.pg = grassland.GrassLand()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())

    def test_getbound(self):
        self.assertIsNotNone(self.pg.getbound("n"))
        self.assertIsNotNone(self.pg.getbound("s"))
        self.assertIsNotNone(self.pg.getbound("w"))
        self.assertIsNotNone(self.pg.getbound("e"))

#    def test_setlayer(self):
# Enought if tested from Playground and e.g. setgrasslayer below..

    def test_createlayer(self):
        #TODO
        self.pg.createlayer("foo")

    def test_getlayer(self):
        self.pg.layers["foo"] = [0]
        self.assertIs(self.pg.layers["foo"], self.pg.getlayer("foo"))

    def test_removelayer(self):
        self.pg.layers["foo"] = [0]
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.pg.removelayer("foo")             
        self.assertFalse(self.pg.layers.has_key("foo"))

#    def tearDown(self):


