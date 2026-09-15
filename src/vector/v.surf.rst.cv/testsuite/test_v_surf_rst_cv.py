#!/usr/bin/env python3

############################################################################
#
# MODULE:       test_v_surf_rst_cv.py
# AUTHOR:       Corey T. White, NCSU GeoForAll Lab
# PURPOSE:      Tests the cross-validation procedure for optimizing
#               v.surf.rst parameters.
# COPYRIGHT:    (C) 2025 OpenPlains Inc. and the GRASS Development Team
#               This program is free software under the GNU General
#               Public License (>=v2). Read the file COPYING that
#               comes with GRASS for details.
#
#############################################################################

import json
import os

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestRSTCrossValidation(TestCase):
    elevation = "elevation"
    points = "test_point_cloud"
    cvdev_prefix = "test_cvdev"
    # Number of CPU cores available to the process, minus one for
    # system stability, capped at 6 for testing
    total_processes = min(6, max(1, len(os.sched_getaffinity(0)) - 1))

    npoints = 500
    segmax = 600

    smooth = [0.5, 5.0]
    tension = [10, 100]

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
        """Remove temporary region, maps, and output files"""
        cls.runModule("g.remove", flags="f", type=["all"], pattern="test_*", quiet=True)
        cls.del_temp_region()
        for output_file in ("test_cv.json", "test_cv.csv"):
            if os.path.exists(output_file):
                os.remove(output_file)

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
            format="csv",
            overwrite=True,
        )
        self.assertModule(module)

        self.assertTrue(module.outputs.stdout)
        lines = module.outputs.stdout.splitlines()
        header = lines[0].split(",")
        self.assertEqual(header[:2], ["tension", "smooth"])
        self.assertEqual(len(lines), 5)
        rmse_index = header.index("rmse")
        rows = {tuple(line.split(",")[:2]): line.split(",") for line in lines[1:]}
        self.assertAlmostEqual(
            float(rows["100", "0.5"][rmse_index]), 2.715355, places=4
        )
        self.assertAlmostEqual(float(rows["10", "0.5"][rmse_index]), 3.938792, places=4)
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
        data = json.loads(module.outputs.stdout)
        self.assertEqual(len(data["results"]), 4)
        self.assertEqual(data["best"]["rmse"]["tension"], 100)
        self.assertEqual(data["best"]["rmse"]["smooth"], 0.5)
        for row in data["results"]:
            self.assertIsNone(row["error"])
            self.assertEqual(row["n"], self.npoints)

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
        for index in range(1, len(self.tension) * len(self.smooth) + 1):
            cvdev_map = f"{self.cvdev_prefix}_{index:03d}"
            self.assertVectorExists(cvdev_map)
            self.assertRasterExists(cvdev_map)

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
        with open("test_cv.json") as json_file:
            data = json.load(json_file)
        self.assertEqual(len(data["results"]), 4)

    def test_save_csv(self):
        """Test saving csv output"""
        module = SimpleModule(
            "v.surf.rst.cv",
            point_cloud=self.points,
            nprocs=self.total_processes,
            smooth=self.smooth,
            tension=self.tension,
            format="csv",
            output_file="test_cv.csv",
            segmax=self.segmax,
            overwrite=True,
        )

        self.assertModule(module)
        with open("test_cv.csv") as csv_file:
            lines = csv_file.read().splitlines()
        self.assertTrue(lines[0].startswith("tension,smooth,"))
        self.assertEqual(len(lines), 5)
        self.assertTrue(module.outputs.stdout)


if __name__ == "__main__":
    test()
