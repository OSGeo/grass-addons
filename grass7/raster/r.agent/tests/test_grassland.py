
import unittest2 as unittest
#import unittest

from libagent import playground, grassland
import grass.script as grass
from grass.script import array as garray

class TestGrassland(unittest.TestCase):
    def setUp(self):
        self.layername = "r.agent.testmap"
        self.pg = grassland.Grassland()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())
        self.assertEqual(self.pg.getregion(),grass.region())

    def test_setregion(self):
        #TODO should not be required here.. maybe "resetregion()"?
        # is set in constructor
        pass

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

    def test_setlayer(self):
        # gets tested in createlayer and super()/Playground
        pass

    def test_setgrasslayer(self):
        # only do this test, if self.layername is set
#        if self.layername:
#            layer = garray.array()
#            retval = layer.write(self.layername)
#            if retval == 1:
#                print "We need a file to play with in this test, but it"
#                print "seems to exist already: '" + self.layername + "'"
#                self.assertTrue(False)
#            self.pg.setgrasslayer(self.layername, self.layername)
#                print "GRASS map layer is already set.."
#            self.pg.setgrasslayer(self.layername, self.layername)
#                print "GRASS map layer was set but no error occured"
#            if not ( self.layers.has_key(self.layername) and \
#                        self.grassmapnames.has_key(self.layername) ):
#                print "GRASS map layer was set but seems missing"
#                self.assertTrue(False)
#            self.pg.setgrasslayer(self.layername, self.layername, True)
#            cleanup..
        pass

    def test_createlayer(self):
        self.pg.createlayer("foo", "foo")
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.assertTrue(self.pg.grassmapnames.has_key("foo"))
        self.assertEqual(len(self.pg.layers["foo"]), self.pg.region["rows"])
        self.assertEqual(len(self.pg.layers["foo"][0]), self.pg.region["cols"])

    def test_getlayer(self):
       # gets tested in createlayer and super()/Playground
        pass

    def test_removelayer(self):
        self.pg.layers["foo"] = [0]
        self.pg.grassmapnames["foo"] = "foo"
        self.assertTrue(self.pg.layers.has_key("foo"))
        self.pg.removelayer("foo")
        self.assertFalse(self.pg.layers.has_key("foo"))
        self.assertFalse(self.pg.grassmapnames.has_key("foo"))

    def test_writelayer(self):
        pass

    def test_parsegrasslayer(self):
        pass

#    def tearDown(self):


