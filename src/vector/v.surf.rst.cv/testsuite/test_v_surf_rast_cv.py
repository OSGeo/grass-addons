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

import os
import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestRSTCrossValidation(TestCase):
    elevation = "elevation"
    points = "test_point_cloud"
    cvdev_prefix = "test_cvdev"
    # Get the number of CPU cores available to the process, minus one for system stability
    total_processes = max(1, len(os.sched_getaffinity(0)) - 1)
    if total_processes > 6:
        # Limit to 6 processes for testing
        total_processes = 6

    # Defaults for interpolation
    npoints = 500
    segmax = 600

    smooth = [0.5, 5.0]
    tension = [10, 100]
    expected_csv = (
        "Tension,Smoothing,RMSE,MAE\n"
        "10,0.5,3.938792429360747,3.2086477739999997\n"
        "10,5.0,4.921535874096144,4.075445157999998\n"
        "100,0.5,2.715355217413409,2.0061099599999994\n"
        "100,5.0,3.438609351379808,2.73388017\n"
    )

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region"""
        # to not override mapset's region (which might be used by other tests)
        cls.use_temp_region()

        cls.runModule(
            "g.region",
            raster=cls.elevation,
            res=30,
            n=220790,
            s=218390,
            w=632680,
            e=635910,
            flags="a",
        )

        cls.runModule(
            "r.random",
            input=cls.elevation,
            npoints=cls.npoints,
            seed=0,
            vector=cls.points,
            flags="z",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove temporary region"""
        cls.runModule("g.remove", flags="f", type=["all"], pattern="test_*", quiet=True)
        cls.del_temp_region()

    def test_v_surf_rst_cv_default(self):
        """Test default settings"""
        module = SimpleModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            segmax=self.segmax,
            overwrite=True,
        )
        self.assertModule(module)

    def test_v_surf_rst_cv_adjust_tension_smooth(self):
        """Test setting tension and smooth"""
        module = SimpleModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            segmax=self.segmax,
            overwrite=True,
        )
        self.assertModule(module)

        self.assertTrue(module.outputs.stdout)
        self.assertMultiLineEqual(self.expected_csv, module.outputs.stdout)
        self.assertTrue(module.outputs.stderr)
        self.assertIn("Tension: 100\n", module.outputs.stderr)
        self.assertIn("Smoothing: 0.5\n", module.outputs.stderr)

    def test_json_format(self):
        """Test json output"""
        module = SimpleModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            segmax=self.segmax,
            format="json",
            overwrite=True,
        )

        self.assertModule(module)
        self.assertTrue(module.outputs.stdout)

    def test_save_cv_vectors(self):
        """Test save cv vectors output"""
        self.assertModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            segmax=self.segmax,
            cv_prefix=self.cvdev_prefix,
            overwrite=True,
        )
        for t in self.tension:
            for s in self.smooth:
                prefix_cv = f"{self.cvdev_prefix}_{t}_{str(s).replace('.', '')}"
                self.assertVectorExists(prefix_cv)
                self.assertRasterExists(f"{prefix_cv}")

    def test_save_json(self):
        """Test saving json output"""
        self.assertModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            segmax=self.segmax,
            format="json",
            output_file="test_cv.json",
            overwrite=True,
        )

    def test_save_csv(self):
        """Test saving csv output"""
        module = SimpleModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            format="text",
            output_file="test_cv.csv",
            segmax=self.segmax,
            overwrite=True,
        )

        self.assertModule(module)
        with open("test_cv.csv", "r") as f:
            lines = f.readlines()
            self.assertTrue(lines[0].startswith("Tension,Smoothing,RMSE,MAE"))
            self.assertTrue(lines[1].startswith("10,0.5,"))
            self.assertTrue(lines[2].startswith("10,5.0,"))
        self.assertTrue(module.outputs.stdout)


if __name__ == "__main__":
    test()
