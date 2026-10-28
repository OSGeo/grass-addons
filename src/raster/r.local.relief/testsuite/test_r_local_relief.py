#!/usr/bin/env python3

"""
MODULE:    Test of r.local.relief

AUTHOR(S): Bhuvan Somisetty <somisettybhuvan5@gmail.com>

PURPOSE:   Test basic operation and bspline mode of r.local.relief

COPYRIGHT: (C) 2026 by Bhuvan Somisetty and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRLocalRelief(TestCase):
    """Test basic operation and bspline mode of r.local.relief"""

    elevation = "elevation"
    output_default = "test_lrm_default"
    output_bspline = "test_lrm_bspline"
    output_shaded = "test_lrm_shaded"
    shaded_relief = "test_lrm_shaded_out"

    @classmethod
    def setUpClass(cls):
        """Setup computational region on a subregion of elevation"""
        cls.use_temp_region()
        cls.runModule(
            "g.region",
            raster=cls.elevation,
            res=20,
            n=220750,
            s=218750,
            w=633000,
            e=635000,
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up raster outputs and restore region"""
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                cls.output_default,
                cls.output_bspline,
                cls.output_shaded,
                cls.shaded_relief,
            ],
        )
        cls.del_temp_region()

    def test_default_mode(self):
        """Test r.local.relief with default r.fillnulls interpolation"""
        self.assertModule(
            "r.local.relief",
            input=self.elevation,
            output=self.output_default,
            neighborhood_size=5,
            overwrite=True,
        )
        self.assertRasterExists(self.output_default)
        info = gs.raster_info(self.output_default)
        self.assertGreater(info["cells"], 0)
        self.assertLess(info["min"], info["max"])

    def test_bspline_mode(self):
        """Test r.local.relief with bspline interpolation (-v flag)"""
        self.assertModule(
            "r.local.relief",
            flags="v",
            input=self.elevation,
            output=self.output_bspline,
            neighborhood_size=5,
            overwrite=True,
        )
        self.assertRasterExists(self.output_bspline)
        info = gs.raster_info(self.output_bspline)
        self.assertGreater(info["cells"], 0)
        self.assertLess(info["min"], info["max"])

    def test_shaded_output(self):
        """Test r.local.relief with shaded output and default color table"""
        self.assertModule(
            "r.local.relief",
            input=self.elevation,
            output=self.output_shaded,
            shaded_output=self.shaded_relief,
            neighborhood_size=5,
            overwrite=True,
        )
        self.assertRasterExists(self.output_shaded)
        self.assertRasterExists(self.shaded_relief)
        info = gs.raster_info(self.shaded_relief)
        self.assertGreater(info["cells"], 0)


if __name__ == "__main__":
    test()
