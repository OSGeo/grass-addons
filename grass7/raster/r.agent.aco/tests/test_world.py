
import unittest2 as unittest
#import unittest

from libagent import world, error

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

    def findposition(self):
        self.assertFalse(self.world.findposition([-1,-1]))
        self.assertNotNone(self.world.findposition([0,0]))
        self.assertEqual(0,*self.world.findposition())

    def test_bear(self):
        self.assertRaises(error.DataError, self.world.bear, *(1, [-1,-1]))
        agent = self.world.bear(1, [0,0])
        self.assertIsInstance(agent, self.world.agenttype)
        self.assertIs(agent, self.world.agents.pop())
        agent = self.world.bear(1)
        self.assertIs(agent, self.world.agents.pop())
        self.assertEqual(0, len(self.world.agents))

    def test_move(self):
        agent = self.world.bear(1, [0,0])
        self.assertRaises(error.DataError, self.world.move, *(agent, [-1,-1]))
        position = [0,0]
        self.world.move(agent, position)
        self.assertEqual(agent.position, position)

    def test_getneighbourpositions(self):
        # gets tested in Playground (except for freedom..).
        pass

    def test_kill(self):
        agent = self.world.bear(1, [0,0])
        self.assertTrue(len(self.world.agents) > 0)
        self.world.kill(agent)
        self.assertTrue(len(self.world.agents) == 0)

#    def tearDown(self):

