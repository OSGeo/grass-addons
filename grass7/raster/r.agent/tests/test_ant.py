
import unittest2 as unittest
#import unittest

from libagent import playground, anthill, ant

class TestAnt(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()
        self.pg.setregion(3,3)
        self.world = anthill.Anthill(self.pg)
        self.world.sites = [[1,1]]
        self.agent = self.world.bear()

    def test_check(self):
        positions = [[0,0],[1,1]]
        self.laststeps = [1,1]
        # An empty test
        self.pg.layers[anthill.Anthill.COST][0][0] = 0
        self.pg.layers[anthill.Anthill.COST][1][1] = 0
        self.assertFalse(self.agent.check(positions))
        self.assertIsNone(self.agent.nextstep[0])
        # set the value of interest but at the homeplace
        self.pg.layers[anthill.Anthill.COST][1][1] = -1
        self.assertFalse(self.agent.check(positions))
        self.assertIsNone(self.agent.nextstep[0])
        # and this time at a good position
        self.pg.layers[anthill.Anthill.COST][0][0] = -1
        self.assertTrue(self.agent.check(positions))
        self.assertIsNotNone(self.agent.nextstep[0])
        self.assertEqual(1, self.agent.nextstep[0])

    def test_choose(self):
        # This one is quite difficult to test as it is mainly a fork of
        # possible other methods which are directly testable
        pass

    def test_walk(self):
        self.agent.position = [0,0]
        self.agent.nextstep = [1,1]
        self.agent.walk()
        self.assertEqual([1,1], self.agent.position)
        self.assertIsNone(self.agent.nextstep[0])
        self.assertLess(0, self.pg.layers[anthill.Anthill.RESULT][1][1])

    def test_work(self):
        # This is the ants main-loop and not that simple to test, every
        # method that is called from here is tested directly
        pass

    def test_setposition(self):
        # This is an Agent method, tested there..
        pass

    def test_getposition(self):
        # This is an Agent method, tested there..
        pass

#    def test_move(self):
        # This is an Agent method, tested there..
#        pass    
    
    def test_age(self):
        # This is an Agent method, tested there..
        pass    
    
    def test_snuffit(self):
        # This is an Agent method, tested there..
        pass

#    def tearDown(self):

