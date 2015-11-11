
import unittest2 as unittest
#import unittest
from math import sqrt
from libagent import playground, error

class TestPlayground(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()

    def test_stringcoordinate(self):
        self.assertEqual(self.pg.stringcoordinate("foo","bar"), [])
        self.assertEqual(self.pg.stringcoordinate("inf","nan"), [])
        self.assertEqual(self.pg.stringcoordinate("2","3"), [3,2])

    def test_setregion(self):
        self.assertTrue(self.pg.region["rows"] == 1)
        self.pg.setregion(2,1)
        self.pg.createlayer("bar")
        self.assertTrue(self.pg.region["rows"] == 2)
        self.assertRaises(error.Error, self.pg.setregion, *[2,1])

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())
        self.assertIs(self.pg.getregion(),self.pg.region)

    def gettotalcount(self):
        #not tested for its just a wrapper
        pass

    def getdiagonalcount(self):
        #not tested for its just a wrapper
        pass

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

    def test_isvalidposition(self):
        self.pg.setregion(3,3)
        self.assertTrue(self.pg.isvalidposition([1,1]))
        self.assertFalse(self.pg.isvalidposition([3,3]))

    def test_addneighbourposition(self):
        self.pg.setregion(3,3)
        positions = []
        ps = positions[:]
        self.assertItemsEqual(ps,
                self.pg.addneighbourposition(positions, [9,9]))
        ps.append([1,1])
        self.assertItemsEqual(ps,
                self.pg.addneighbourposition(positions, [1,1]))

    def test_getorderedneighbourpositions(self):
        self.pg.setregion(3,3)
        self.assertFalse(self.pg.getorderedneighbourpositions([1,1],3))

        ps = self.pg.getorderedneighbourpositions([2,2],4)
        self.assertEqual(2, len(ps))
        self.assertEqual(0, ps[1][3])

        ps = self.pg.getorderedneighbourpositions([1,1],8)
        self.assertEqual(8, len(ps))
        self.assertEqual(7, ps[7][2])
        self.assertEqual(0, ps[3][3])
        self.assertEqual(sqrt(2)-1, ps[6][3])

    def test_getneighbourpositions(self):
        self.pg.setregion(3,3)
        ps = self.pg.getneighbourpositions([2,2],4)
        self.assertEqual(2, len(ps))
        self.assertEqual(0, ps[1][3])

    def test_getcellvalue(self):
        l = "bar"
        self.pg.createlayer(l)
        self.pg.layers[l][0][0] = 0
        self.assertNotEqual(101, self.pg.getcellvalue(l, [0,0]))
        self.pg.layers[l][0][0] = 101
        self.assertEqual(101, self.pg.getcellvalue(l, [0,0]))

    def test_setcellvalue(self):
        l = "bar"
        self.pg.createlayer(l)
        self.pg.layers[l][0][0] = 0
        self.assertNotEqual(101, self.pg.layers[l][0][0])
        self.pg.setcellvalue(l, [0,0], 101)
        self.assertEqual(101, self.pg.getcellvalue(l, [0,0]))

    def test_decaycellvalues(self):
        l = "bar"
        self.pg.createlayer(l)
        self.pg.layers[l][0][0] = 100
        self.pg.decaycellvalues(l, 3)
        self.assertEqual(int(round(self.pg.layers[l][0][0])), 79)
        self.pg.decaycellvalues(l, 3)
        self.assertEqual(int(round(self.pg.layers[l][0][0])), 63)
        self.pg.decaycellvalues(l, 3)
        self.assertEqual(int(round(self.pg.layers[l][0][0])), 50)

#    def tearDown(self):

