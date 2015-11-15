
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
        self.agent.laststeps = [[1,1]]
        # An empty test
        self.pg.layers[anthill.Anthill.SITE][0][0] = 0
        self.pg.layers[anthill.Anthill.SITE][1][1] = 0
        self.assertFalse(self.agent.check(positions))
        self.assertIsNone(self.agent.nextstep[0])
        self.assertEqual(0, self.world.numberofpaths)
        # set the value of interest but at the homeplace
        self.pg.layers[anthill.Anthill.SITE][1][1] = -1
        self.assertFalse(self.agent.check(positions))
        self.assertIsNone(self.agent.nextstep[0])
        self.assertEqual(0, self.world.numberofpaths)
        # and this time at a good position
        self.pg.layers[anthill.Anthill.SITE][0][0] = -1
        self.assertTrue(self.agent.check(positions))
        self.assertIsNotNone(self.agent.nextstep[0])
        self.assertEqual(1, self.agent.nextstep[0])
        self.assertEqual(1, self.world.numberofpaths)

    def test_markedpositions(self):
        self.world.pheroweight = 1
        # we do not explicitly test random here..
        self.world.randomweight = 1
        self.world.minrandom = 0
        self.world.maxrandom = 1
        positions = [[0,0,0,0],[1,1,3,0]]
        self.pg.layers[anthill.Anthill.RESULT][0][0] = 0
        self.pg.layers[anthill.Anthill.RESULT][1][1] = 999
        p = self.agent.markedposition(positions)
        self.assertEqual([1,1], p[:2])

    def test_costlymarkedpositions(self):
        self.world.costweight = 1
        # we do not test random or pheromone at all here..
        self.world.pheroweight = 0
        self.world.randomweight = 0
        positions = [[0,0,0,0],[1,1,3,0]]
        self.pg.layers[anthill.Anthill.COST][0][0] = 0
        self.pg.layers[anthill.Anthill.COST][1][1] = 2
        p = self.agent.costlymarkedposition(positions)
        self.assertEqual([0,0], p[:2])
        # test if min/max works
        self.world.minpenalty = 1
        self.world.maxpenalty = 3
        p = self.agent.costlymarkedposition(positions)
        self.assertEqual([1,1], p[:2])
        # now test if the ant is really dying if min/max wrong
        self.world.minpenalty = 3
        self.assertLess(p[3],1)
        p = self.agent.costlymarkedposition(positions)
        self.assertGreater(p[3],1)

    def test_choose(self):
        # every second step should be a goal..
        self.assertEqual(0, self.world.numberofpaths)
        self.pg.layers[anthill.Anthill.SITE][0][0] = -1
        self.pg.layers[anthill.Anthill.SITE][2][0] = -1
        self.pg.layers[anthill.Anthill.SITE][0][2] = -1
        self.pg.layers[anthill.Anthill.SITE][2][2] = -1
        self.world.sites = [[0,0],[2,0],[0,2],[2,2]]
        self.agent = self.world.bear()
        # we exclude home here to be a goal node, as the return
        # statement in choose is mainly a shortcut and a goal node
        # so close to home just does not make much sense
        self.pg.layers[anthill.Anthill.SITE]\
            [self.agent.position[0]][self.agent.position[1]] = 0
        self.assertIsNone(self.agent.nextstep[0])
        self.agent.choose()
        self.assertIsNotNone(self.agent.nextstep[0])
        self.agent.laststeps.append(self.agent.position)
        self.agent.position = self.agent.nextstep
        self.agent.nextstep = [None,None,None,0]
        self.agent.choose()
        self.assertEqual(1, self.world.numberofpaths)

    def test_walkhome(self):
        self.agent.nextstep = [0,0,0,0]
        self.agent.laststeps = [[1,1,0,0], [0,1,0,0]]
        self.agent.walkhome()
        self.assertEqual(self.world.pathintensity,
                self.pg.layers[anthill.Anthill.RESULT][0][0])
        self.assertEqual([[1,1,0,0]], self.agent.laststeps)
        self.agent.walkhome()
        self.assertEqual(0, len(self.world.agents))
        self.world.antavoidsloops = False
        self.agent.laststeps = [[1,1,0,0], [0,1,0,0], [1,1,0,0]]
        self.agent.walkhome()
        expected = [[1,1,0,0], [0,1,0,0]]
        self.assertEqual(expected, self.agent.laststeps)
        self.world.antavoidsloops = True
        self.agent.laststeps = [[1,1,0,0], [0,1,0,0], [1,1,0,0]]
        self.agent.walkhome()
        expected = []
        self.assertEqual(expected, self.agent.laststeps)

    def test_walkaround(self):
        self.agent.position = [0,0]
        self.agent.nextstep = [1,1]
        self.agent.walk()
        self.assertEqual([1,1], self.agent.position)
        self.assertIsNone(self.agent.nextstep[0])
        self.assertLess(0, self.pg.layers[anthill.Anthill.RESULT][1][1])

    def test_work(self):
        # This is the ants main-loop and not that simple to test, every
        # method that is called from here is tested directly
        #
        # every second step should be a goal..
        # (also see test_choose)
        self.assertEqual(0, self.world.numberofpaths)
        # see test_choose() for why we exclude home here
        self.pg.layers[anthill.Anthill.SITE][0][0] = 0
        self.pg.layers[anthill.Anthill.SITE][2][1] = -1
        self.pg.layers[anthill.Anthill.SITE][1][2] = -1
        self.world.sites = [[0,0],[2,1],[1,2]]
        self.agent = ant.Ant(1, self.world, [0,0])
        self.world.agents.append(self.agent)
        self.assertIsNone(self.agent.nextstep[0])
        self.agent.work()
        self.assertEqual(0, self.agent.ttl)
        self.agent.ttl = 1
        self.agent.work()
        if self.agent.nextstep[0] is None:
            self.agent.ttl = 1
            self.agent.work()
        self.assertIsNotNone(self.agent.nextstep[0])
        self.assertEqual(1, self.world.numberofpaths)

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

    def tearDown(self):
        self.pg = None
        self.world = None
        self.agent = None

