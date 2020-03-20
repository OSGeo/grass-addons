#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.ml

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.ml for regression

COPYRIGHT: (C) 2020 by Steven Pawley and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""
import tempfile
import os

import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRegression(TestCase):
    """Test regression and prediction using r.learn.ml"""

    # input rasters
    band1 = "lsat7_2002_10@PERMANENT"
    band2 = "lsat7_2002_20@PERMANENT"
    band3 = "lsat7_2002_30@PERMANENT"
    band4 = "lsat7_2002_40@PERMANENT"
    band5 = "lsat7_2002_50@PERMANENT"
    band7 = "lsat7_2002_70@PERMANENT"
    input_map = "elev_ned_30m@PERMANENT"

    # imagery group created during test
    group = "predictors"

    # training data created during test
    training_points = "training_points"

    # raster map created as output during test
    output = "regression_result"

    # files created during test
    model_file = tempfile.NamedTemporaryFile(suffix=".gz").name
    training_file = tempfile.NamedTemporaryFile(suffix=".gz").name

    @classmethod
    def setUpClass(cls):
        """Setup that is required for all tests
        
        Uses a temporary region for testing and creates an imagery group and randomly samples a
        categorical map to use as training pixels/points
        """
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.input_map)
        cls.runModule(
            "i.group",
            group=cls.group,
            input=[cls.band1, cls.band2, cls.band3, cls.band4, cls.band5, cls.band7],
        )
        cls.runModule(
            "r.random",
            input=cls.input_map,
            npoints=1000,
            vector=cls.training_points,
            seed=1234,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        cls.del_temp_region()
        cls.runModule("g.remove", flags="f", type="vector", name=cls.training_points)
        cls.runModule("g.remove", flags="f", type="group", name=cls.group)

    def tearDown(self):
        """Remove the output created from the tests
        (reuse the same name for all the test functions)"""
        self.runModule("g.remove", flags="f", type="raster", name=[self.output])

        try:
            os.remove(self.model_file)
        except FileNotFoundError:
            pass

        try:
            os.remove(self.training_file)
        except FileNotFoundError:
            pass

    def test_output_created_regression(self):
        """Checks that the output is created"""
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_points=self.training_points,
            field="value",
            model_name="RandomForestRegressor",
            n_estimators=100,
            save_model=self.model_file,
        )
        self.assertFileExists(filename=self.model_file)

        self.assertModule(
            "r.learn.predict",
            group=self.group,
            load_model=self.model_file,
            output=self.output,
        )
        self.assertRasterExists(self.output, msg="Output was not created")

    def test_save_load_training(self):
        """Test that training data can be saved and loaded"""

        # save training data
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_points=self.training_points,
            field="value",
            model_name="RandomForestRegressor",
            save_training=self.training_file,
            n_estimators=100,
            save_model=self.model_file,
        )
        self.assertFileExists(filename=self.model_file)
        self.assertFileExists(filename=self.training_file)

        # load training data and retrain
        self.assertModule(
            "r.learn.train",
            group=self.group,
            model_name="RandomForestRegressor",
            load_training=self.training_file,
            n_estimators=100,
            save_model=self.model_file,
            overwrite=True
        )

        # predict after loading training data
        self.assertModule(
            "r.learn.predict",
            group=self.group,
            load_model=self.model_file,
            output=self.output,
        )
        self.assertRasterExists(self.output, msg="Output was not created")


if __name__ == "__main__":
    test()
