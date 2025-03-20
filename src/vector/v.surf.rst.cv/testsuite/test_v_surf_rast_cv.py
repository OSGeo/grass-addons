#!/usr/bin/env python3

############################################################################
#
# MODULE:       test_r_hand.py
# AUTHOR:       Corey T. White, NCSU GeoForAll Lab
# PURPOSE:      Performs cross-validation proceedure to optimize the
#               parameterization of v.surf.rst tension and smoothing
#               paramters.
# COPYRIGHT:    (C) 2025 OpenPlains Inc. and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################


import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestRSTCrossValidation(TestCase):
    elevation = "elevation"
    stream_rast = "test_stream_rast"
    direction = "test_direction"
    hand = "test_hand"
    inundation = "test_inundation"
    inundation_strds = "test_inundation_strds"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()

        cls.runModule(
            "g.region",
            raster=cls.elevation,
            res=10,
            n=220790,
            s=218390,
            w=632680,
            e=635910,
            flags="a",
        )

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.runModule("g.remove", flags="f", type="all", pattern="test_*")
        cls.del_temp_region()

    def test_v_surf_rst_cv_default(self):
        """Test default settings"""
        self.assertModule(
            "v.surf.rst.cv",
            point_cloud="elevation",
            overwrite=True,
        )
        self.assertRasterExists(self.inundation)


if __name__ == "__main__":
    test()
