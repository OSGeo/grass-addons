import unittest2 as unittest

# import unittest

from libagent import playground, world, agent


class TestAgent(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()
        self.pg.setregion(3, 3)
        self.world = world.World(self.pg, None)
        self.world.bear(1, [1, 1], agent.Agent)
        self.agent = self.world.agents[0]

    def test_setposition(self):
        self.assertTrue(self.agent.getposition() == [1, 1])
        self.agent.setposition([3, 3])
        self.assertTrue(self.agent.getposition() == [3, 3])

    def test_getposition(self):
        self.assertTrue(self.agent.getposition() == [1, 1])

    def test_randomposition(self):
        position = [1, 2]
        self.assertEqual(position, self.agent.randomposition([position, position]))

    def test_step(self):
        position = self.agent.getposition()
        oldposition = [position[0], position[1]]
        agentneighbours = self.world.getneighbourpositions(position)
        for i in range(len(agentneighbours)):
            p = [agentneighbours[i][0], agentneighbours[i][1]]
            agentneighbours[i] = p

        self.agent.step()
        newposition = self.agent.getposition()
        self.assertIn(newposition, agentneighbours)
        self.assertFalse(newposition == oldposition)

    def test_age(self):
        self.agent.ttl = 1
        age = self.agent.ttl
        self.agent.age()
        self.assertTrue(self.agent.ttl < age)
        self.agent.age()
        self.assertTrue(len(self.world.agents) == 0)

    def test_snuffit(self):
        self.assertTrue(len(self.world.agents) == 1)
        self.agent.snuffit()
        self.assertTrue(len(self.world.agents) == 0)


#    def tearDown(self):
