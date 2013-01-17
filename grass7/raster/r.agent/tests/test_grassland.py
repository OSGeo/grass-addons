
import unittest2 as unittest
#import unittest

from libagent import playground, grassland
import grass.script as grass
from grass.script import array as garray

class TestGrassLand(unittest.TestCase):
    def setUp(self):              
        self.pg = grassland.GrassLand()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())
        self.assertEqual(self.pg.getregion(),grass.region())

    def test_getbound(self):
        n = self.pg.region["n"]
        s = self.pg.region["s"]
        w = self.pg.region["w"]
        e = self.pg.region["e"]
        ns = self.pg.region["nsres"]
        ew = self.pg.region["ewres"]
        r = self.pg.region["rows"]
        c = self.pg.region["cols"]
                            
        self.assertIsNotNone(n)
        self.assertIsNotNone(s)
        self.assertIsNotNone(w)
        self.assertIsNotNone(e)
        self.assertTrue(n>s)
        self.assertTrue(e>w)

        self.assertEqual((n-s)/ns, r)
        self.assertEqual((e-w)/ew, c)

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

    #def test_getlayer(self):
       # gets tested in createlayer and super()/Playground

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


