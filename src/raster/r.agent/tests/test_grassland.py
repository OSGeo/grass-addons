import unittest2 as unittest

# import unittest

from libagent import error, playground, grassland
import grass.script as grass
from grass.script import array as garray


class TestGrassland(unittest.TestCase):
    def setUp(self):
        # TODO check if there is a nicer way to do this..
        self.rastlayername = None  # "r_agent_rast_testmap@"+grass.gisenv()['MAPSET']
        self.vectlayername = None  # "r_agent_vect_testmap@"+grass.gisenv()['MAPSET']

        if self.rastlayername:
            for m in grass.list_strings("rast"):
                if self.rastlayername == m:
                    print("We need a raster map to play with in this test," + " but it seems to exist already: '" + self.rastlayername + "'")
                    self.assertTrue(False)

        if self.vectlayername:
            for m in grass.list_strings("vect"):
                if self.vectlayername == m:
                    print("We need a vector map to play with in this test," + " but it seems to exist already: '" + self.vectlayername + "'")
                    self.assertTrue(False)

        self.pg = grassland.Grassland()

    def test_getregion(self):
        self.assertIsNotNone(self.pg.getregion())
        self.assertEqual(self.pg.getregion(), grass.region())

    def test_setregion(self):
        # TODO should not be required here.. maybe "resetregion()"?
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
        self.assertTrue(n > s)
        self.assertTrue(e > w)

        self.assertEqual((n - s) / ns, r)
        self.assertEqual((e - w) / ew, c)

    def test_setlayer(self):
        # gets tested in createlayer and super()/Playground
        pass

    def test_setgrasslayer(self):
        # only do this test, if self.rastlayername is set
        if self.rastlayername:
            layer = garray.array()
            # set the layer
            ## the first time it is missing
            self.assertRaises(
                error.DataError,
                self.pg.setgrasslayer,
                *[self.rastlayername, self.rastlayername]
            )
            ## so we need to write it first
            pass

    # TODO
    ## the second time it should be added correctly

    ## now test whether it fails the third time
    #            self.assertRaises(error.Error, self.pg.setgrasslayer,
    #                                    *[self.rastlayername, self.rastlayername])
    #            if not ( self.pg.layers.has_key(self.rastlayername) and \
    #                        self.pg.grassmapnames.has_key(self.rastlayername) ):
    #                print "GRASS map layer was set but seems missing"
    #                self.assertTrue(False)
    # set it once more, this time forcing it
    #            self.pg.setgrasslayer(self.rastlayername, self.rastlayername, True)

    def test_createlayer(self):
        self.pg.createlayer("foo", "foo")
        self.assertTrue("foo" in self.pg.layers)
        self.assertTrue("foo" in self.pg.grassmapnames)
        self.assertEqual(len(self.pg.layers["foo"]), self.pg.region["rows"])
        self.assertEqual(len(self.pg.layers["foo"][0]), self.pg.region["cols"])

    def test_getlayer(self):
        # gets tested in createlayer and super()/Playground
        pass

    def test_removelayer(self):
        self.pg.layers["foo"] = [0]
        self.pg.grassmapnames["foo"] = "foo"
        self.assertTrue("foo" in self.pg.layers)
        self.pg.removelayer("foo")
        self.assertFalse("foo" in self.pg.layers)
        self.assertFalse("foo" in self.pg.grassmapnames)

    def test_writelayer(self):
        if self.rastlayername:
            # create an empty test map
            layer = garray.array()
            self.pg.createlayer(self.rastlayername, self.rastlayername)
            # write it once
            self.pg.writelayer(self.rastlayername)
            # now remove it from the internal grasslayer list
            self.pg.grassmapnames.pop(self.rastlayername)
            self.assertRaises(error.DataError, self.pg.writelayer, self.rastlayername)
            # try again, this time being explicit, but still fail
            self.assertRaises(
                error.DataError,
                self.pg.writelayer,
                *[self.rastlayername, self.rastlayername]
            )
            # force write it again..
            self.pg.writelayer(self.rastlayername, self.rastlayername, True)

    def test_parsevectorlayer(self):
        if self.vectlayername:
            # TODO find a way to write vector files..
            pass

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
        self.pg.decaycellvalues(l, 3, 50)
        self.assertEqual(int(round(self.pg.layers[l][0][0])), 50)

    def tearDown(self):
        if self.rastlayername:
            grass.try_remove(
                grass.find_file(name=self.rastlayername, element="cell")["file"]
            )
        if self.vectlayername:
            grass.try_remove(
                grass.find_file(name=self.vectlayername, element="vector")["file"]
            )
