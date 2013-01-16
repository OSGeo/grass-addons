
import unittest2 as unittest
#import unittest

from libagent import playground

class TestOurExceptions(unittest.TestCase):
    def setUp(self):
        self.pg = playground.Playground()

    def test_getregion(self):
        self.pg.getregion()

#    def tearDown(self):


