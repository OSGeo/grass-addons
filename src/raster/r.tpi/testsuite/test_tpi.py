#!/usr/bin/env python3

"""
MODULE:    Test of r.tpi

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.tpi basic operation

COPYRIGHT: (C) 2022 by Steven Pawley and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""
import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestClassification(TestCase):
    """Test basic operation of r.tpi"""

    # input rasters
    dem_map = "elevation"
    tpi_map = "mtpi"

    @classmethod
    def setUpClass(cls):
        """Setup that is required for all tests"""
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.dem_map)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        cls.del_temp_region()
        cls.runModule("g.remove", flags="f", type="raster", name=cls.tpi_map)

    def test_mtpi(self):
        """Checks that the output is created"""
        # train model
        self.assertModule(
            "r.tpi",
            input=self.dem_map,
            minradius=1,
            maxradius=31,
            steps=5,
            output=self.tpi_map,
        )
        self.assertRasterExists(self.tpi_map, msg="Output was not created")


if __name__ == "__main__":
    test()
