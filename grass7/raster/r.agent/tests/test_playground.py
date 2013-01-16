
import unittest2 as unittest
#import unittest

from libagent import playground

class TestOurExceptions(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())

    def test_getbound(self):
        self.assertIsNotNone(self.pg.getbound("n"))
        self.assertIsNotNone(self.pg.getbound("s"))
        self.assertIsNotNone(self.pg.getbound("w"))
        self.assertIsNotNone(self.pg.getbound("e"))

    def test_setlayer(self):
        layer = [0]
        key = "foo"
        self.pg.setlayer(key, layer)
        self.assertIs(self.pg.layers[key], layer)
        self.assertRaises(Exception,  self.pg.setlayer, (key, layer))
        layer = [0]
        self.assertIsNot(self.pg.layers[key], layer)
        self.pg.setlayer(key, layer, True)
        self.assertIs(self.pg.layers[key], layer)

#    def tearDown(self):

