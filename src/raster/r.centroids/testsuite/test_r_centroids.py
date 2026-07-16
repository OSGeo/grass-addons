#!/usr/bin/env python

############################################################################
#
# NAME:      r_centroids_test
#
# AUTHOR:    Caitlin Haedrich (caitlin dot haedrich gmail com)
#
# PURPOSE:   This is a test file for r.centroids
#
# SPDX-FileCopyrightText: 2021 Caitlin Haedrich
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#############################################################################

# Dependencies
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


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
        cls.runModule("g.region", raster="basin")

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.del_temp_region()

    def tearDown(self):
        """
        Remove the outputs created from the centroids module
        This is executed after each test run.
        """
        self.runModule("g.remove", flags="f", type="vector", name=self.centroids)

    def test_output(self):
        """Test that centroids are expected output"""
        # assertModule is used to call module which we test
        # we expect module to finish successfully
        self.assertModule(
            "r.centroids", input="basin", output=self.centroids, overwrite=True
        )

        self.assertVectorEqualsAscii(
            self.centroids, "data/r_centroids_reference.txt", digits=6, precision=1
        )


if __name__ == "__main__":
    test()
