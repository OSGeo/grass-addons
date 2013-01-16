
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
        self.assertTrue(self.pg.getbound("n")>self.pg.getbound("s"))
        self.assertTrue(self.pg.getbound("e")>self.pg.getbound("w"))

    #def test_setlayer(self):
       # gets tested in createlayer and super()/Playground

    def test_setgrasslayer(self):
        #TODO better test manually?
        pass

    def test_createlayer(self):
        self.pg.createlayer("foo", "foo")
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.assertTrue(self.pg.grassmapnames.has_key("foo"))
        self.assertEqual(len(self.pg.layers["foo"]), self.pg.region["rows"])
        self.assertEqual(len(self.pg.layers["foo"][0]), self.pg.region["cols"])

    def test_getlayer(self):
        self.pg.layers["foo"] = [0]
        self.assertIs(self.pg.layers["foo"], self.pg.getlayer("foo"))

    def test_removelayer(self):
        self.pg.layers["foo"] = [0]
        self.pg.grassmapnames["foo"] = "foo"
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.pg.removelayer("foo")             
        self.assertFalse(self.pg.layers.has_key("foo"))
        self.assertFalse(self.pg.grassmapnames.has_key("foo"))

    def test_writelayer(self):
        #TODO better test manually?
        pass

#    def tearDown(self):


