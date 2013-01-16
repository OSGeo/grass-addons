
import unittest2 as unittest
#import unittest

from libagent import playground, error

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
        self.assertRaises(error.Error, self.pg.setlayer, *[key, layer])
        layer = [0]
        self.assertIsNot(self.pg.layers[key], layer)
        self.pg.setlayer(key, layer, True)
        self.assertIs(self.pg.layers[key], layer)

    def test_createlayer(self):
        #TODO from file, better test manually?
        self.pg.createlayer("foo")
        self.assertTrue(self.pg.layers.has_key("foo"))
        #TODO rows / cols

    def test_getlayer(self):
        self.pg.layers["foo"] = [0]
        self.assertIs(self.pg.layers["foo"], self.pg.getlayer("foo"))

    def test_removelayer(self):
        self.pg.layers["foo"] = [0]
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.pg.removelayer("foo")
        self.assertFalse(self.pg.layers.has_key("foo"))

    def test_writelayer(self):
        #TODO better test manually?
        pass

#    def tearDown(self):

