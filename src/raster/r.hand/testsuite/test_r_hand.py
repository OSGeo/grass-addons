#!/usr/bin/env python3

############################################################################
#
# MODULE:       test_r_hand.py
# AUTHOR:       Corey T. White, OpenPlains Inc.
# PURPOSE:      Performs Height Above Nearest Drainage (HAND) analysis.
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


class TestHand(TestCase):
    elevation = "elevation"
    stream_rast = "test_stream_rast"
    direction = "test_direction"
    hand = "test_hand"
    inundation = "test_inundation"
    inundation_strds = "test_inundation_strds"
    inundation_strds_maps = [
        "test_inundation_strds_0.0",
        "test_inundation_strds_1.0",
        "test_inundation_strds_2.0",
        "test_inundation_strds_3.0",
    ]

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
        cls.runModule(
            "r.watershed",
            elevation=cls.elevation,
            threshold=50000,
            stream=cls.stream_rast,
            drainage=cls.direction,
            quiet=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.runModule("g.remove", flags="f", type="all", pattern="test_*")
        cls.del_temp_region()

    def test_r_hand_default(self):
        """Test default settings"""
        self.assertModule(
            "r.hand",
            elevation=self.elevation,
            depth=2,
            inundation_raster=self.inundation,
            overwrite=True,
        )
        self.assertRasterExists(self.inundation)

    def test_r_hand_no_depth(self):
        """Test expect failing for no depth set"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            inundation_raster=self.inundation,
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Inundation depth must be greater than 0", module.outputs.stderr)

    def test_r_hand_negative_depth(self):
        """Test expect failing for depth less than 0"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            inundation_raster=self.inundation,
            depth=-1,
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Inundation depth must be greater than 0", module.outputs.stderr)

    def test_r_hand_no_watershed(self):
        """Test should use user provided streams and flow directions"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_raster=self.inundation,
            depth=3,
            overwrite=True,
        )
        self.assertModule(module)
        # self.assertTrue(module.outputs.stdout)
        # self.assertNotIn("Generating streams and flow direction raster maps", module.outputs.stdout)
        self.assertRasterExists(self.inundation)

    def test_r_hand_save_differenc(self):
        """Test to ensure hand raster is saved"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_raster=self.inundation,
            hand=self.hand,
            depth=3,
            overwrite=True,
        )
        self.assertModule(module)
        self.assertRasterExists(self.hand)
        self.assertRasterExists(self.inundation)

    def test_r_hand_series(self):
        """Test series of inundation rasters"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            start_water_level=0.0,
            end_water_level=3.0,
            water_level_step=1,
            flags="t",
            overwrite=True,
        )
        self.assertModule(module)
        self.assertRasterExists(self.hand)
        for i in self.inundation_strds_maps:
            self.assertRasterExists(i)

    def test_r_hand_series_no_start(self):
        """Test expected failure for no start water level"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            # start_water_level=0,
            end_water_level=3,
            water_level_step=1,
            flags="t",
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Start water level must be provided", module.outputs.stderr)

    def test_r_hand_series_no_end(self):
        """Test expected failure for no end water level"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            start_water_level=0,
            # end_water_level=3,
            water_level_step=1,
            flags="t",
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("End water level must be provided", module.outputs.stderr)

    def test_r_hand_series_neg_start_value(self):
        """Test expected failure for negative start water level"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            start_water_level=-4,
            end_water_level=3,
            water_level_step=1,
            flags="t",
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Start water level must be greater than 0", module.outputs.stderr)

    def test_r_hand_series_neg_start_value(self):
        """Test expected failure for start water level > end water level"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            start_water_level=5,
            end_water_level=0,
            water_level_step=1,
            flags="t",
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn(
            "Start water level must be less than end water level", module.outputs.stderr
        )

    def test_r_hand_series_neg_water_level_step(self):
        """Test expected failure for negative water level step"""

        module = SimpleModule(
            "r.hand",
            elevation=self.elevation,
            streams=self.stream_rast,
            direction=self.direction,
            inundation_strds=self.inundation_strds,
            hand=self.hand,
            start_water_level=0,
            end_water_level=5,
            water_level_step=-1,
            flags="t",
            overwrite=True,
        )
        self.assertModuleFail(module)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Water level step must be greater than 0", module.outputs.stderr)


if __name__ == "__main__":
    test()
