
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

    def test_setposition(self):
        pass

    def test_getposition(self):
        pass

    def test_move(self):
        pass    
    
    def test_age(self):
        pass    
    
    def test_snuffit(self):
        pass

    def test_walk(self):
        pass

    def test_work(self):
        pass

#    def tearDown(self):

