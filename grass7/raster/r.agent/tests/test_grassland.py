
import unittest2 as unittest
#import unittest

from libagent import playground, grassland

class TestOurExceptions(unittest.TestCase):
    def setUp(self):              
        self.pg = grassland.GrassLand()

    def test_getregion(self):
        self.pg.getregion()

#    def tearDown(self):


