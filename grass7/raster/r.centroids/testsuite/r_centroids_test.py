#!/usr/bin/env python

############################################################################
#
# NAME:      r_centroids_test
#
# AUTHOR:    Caitlin Haedrich (caitlin dot haedrich gmail com)
#
# PURPOSE:   This is a test file for r.centroids
#
# COPYRIGHT: (C) 2021 by Caitlin Haedrich and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

# Dependencies
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.script.core import read_command
import os

# Expected outcome
CENTROIDS_TABLE = """642375|226865|2\r\r\n643425|223335|4\r\r\n642175|222595|6\r\r\n640185|225145|8\r\r\n641555|222725|10\r\r\n635555|224365|12\r\r\n638965|221925|14\r\r\n641785|220725|16\r\r\n635085|217465|18\r\r\n632215|220135|20\r\r\n632285|216115|22\r\r\n637495|216175|24\r\r\n640835|217145|26\r\r\n636595|219745|28\r\r\n639795|219545|30\r\r\n"""

# Tests
class TestCentroids(TestCase):
    # Setup variables to be used for outputs
    centroids = "test_centroids"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()
        # cls.runModule or self.runModule is used for general module calls
        cls.runModule('g.region', raster='elevation')


    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    @classmethod
    def tearDown(self):
        """
        Remove the outputs created from the centroids module
        This is executed after each test run.
        """
        self.runModule(
            "g.remove",
            flags="f",
            type="vector",
            name=self.centroids
        )

    def test_output(self):
        """Test that centroids are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            'r.centroids',
            input='basins',
            output=self.centroids,
            overwrite=True
            )
        
        test_centroid_table = read_command("v.out.ascii", input=self.centroids, format="point")

        self.assertEqual(
            CENTROIDS_TABLE,
            test_centroid_table)
        

if __name__ == '__main__':
    test()