#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.ml

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.ml for valid parameters

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


class TestParameters(TestCase):
    """Test for valid parameters using r.learn.ml"""

    # input rasters
    band1 = "lsat7_2002_10@PERMANENT"
    band2 = "lsat7_2002_20@PERMANENT"
    band3 = "lsat7_2002_30@PERMANENT"
    band4 = "lsat7_2002_40@PERMANENT"
    band5 = "lsat7_2002_50@PERMANENT"
    band7 = "lsat7_2002_70@PERMANENT"
    classif_map = "landclass96@PERMANENT"

    # imagery group created during test
    group = "predictors"

    # training data created during test
    labelled_pixels = "training_pixels"
    labelled_points = "training_points"

    # raster map created as output during test
    output = "classification_result"

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
        cls.runModule("g.region", raster=cls.classif_map)
        cls.runModule(
            "i.group",
            group=cls.group,
            input=[cls.band1, cls.band2, cls.band3, cls.band4, cls.band5, cls.band7],
        )
        cls.runModule(
            "r.random",
            input=cls.classif_map,
            npoints=1000,
            raster=cls.labelled_pixels,
            seed=1234,
        )
        cls.runModule(
            "r.to.vect",
            input=cls.labelled_pixels,
            output=cls.labelled_points,
            type="point",
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        cls.del_temp_region()
        cls.runModule("g.remove", flags="f", type="raster", name=cls.labelled_pixels)
        cls.runModule("g.remove", flags="f", type="vector", name=cls.labelled_points)
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

    def test_train_missing_parameter(self):
        """Check that module fails when parameters are missing"""

        # missing group
        self.assertModuleFail(
            "r.learn.train",
            training_points=self.labelled_points,
            field="value",
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
        )

        # missing any training data
        self.assertModuleFail(
            "r.learn.train",
            group=self.group,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
        )

        # using points as input but no field specified
        self.assertModuleFail(
            "r.learn.train",
            group=self.group,
            training_points=self.labelled_points,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
        )

        # using both points and labelled pixels
        self.assertModuleFail(
            "r.learn.train",
            group=self.group,
            training_points=self.labelled_points,
            training_map=self.labelled_pixels,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
        )

        # no model output
        self.assertModuleFail(
            "r.learn.train",
            group=self.group,
            training_points=self.labelled_points,
            model_name="RandomForestClassifier",
            n_estimators=100,
        )


if __name__ == "__main__":
    test()
