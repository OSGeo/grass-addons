
import unittest2 as unittest
#import unittest

from libagent import world

class TestWorld(unittest.TestCase):
    def setUp(self):
        self.world = world.World()

    def test_addlayertopg(self):
        self.world.addlayertopg("foo")
        self.assertTrue(len(self.world.playground.layers["foo"]) > 0)

    def test_removelayerfrompg(self):
        self.world.addlayertopg("foo")
        self.assertTrue(self.world.playground.layers.has_key("foo"))
        self.world.removelayerfrompg("foo")
        self.assertFalse(self.world.playground.layers.has_key("foo"))

    def test_getlayer(self):
        self.world.addlayertopg("foo")
        self.assertIs(self.world.getlayer("foo"),
                        self.world.playground.layers["foo"])

    def test_bear(self):
        agent = self.world.bear(1, [1,1])
        self.assertIsInstance(agent, self.world.agenttype)
        self.assertIs(agent, self.world.agents.pop())

    def test_move(self):
        pass

    def test_getposition(self):
        pass

    def test_getneighbourpositions(self):
        pass

    def test_kill(self):
        pass

#    def tearDown(self):

