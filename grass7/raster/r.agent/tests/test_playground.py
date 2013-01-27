
import unittest2 as unittest
#import unittest

from libagent import playground, error

class TestPlayground(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())
        self.assertIs(self.pg.getregion(),self.pg.region)

    def test_getbound(self):
        n = self.pg.region["n"]
        s = self.pg.region["s"]
        w = self.pg.region["w"]
        e = self.pg.region["e"]
        #TODO needed?
#        ns = self.pg.region["nsres"]
        ns = 1
#        ew = self.pg.region["ewres"]
        ew = 1
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
        self.assertEqual(len(self.pg.layers["foo"]), self.pg.region["rows"])
        self.assertEqual(len(self.pg.layers["foo"][0]), self.pg.region["cols"])

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

    def test_getrandomposition(self):
        n = self.pg.region["n"]
        s = self.pg.region["s"]
        w = self.pg.region["w"]
        e = self.pg.region["e"]

        position = self.pg.getrandomposition()
        self.assertTrue(position[0] >= s)
        self.assertTrue(position[0] < n)
        self.assertTrue(position[1] >= w)
        self.assertTrue(position[1] < e)

#    def tearDown(self):

