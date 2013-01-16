
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

#    def tearDown(self):


