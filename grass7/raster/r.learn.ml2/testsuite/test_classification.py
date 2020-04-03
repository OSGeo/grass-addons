#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.ml

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.ml for classification

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


class TestClassification(TestCase):
    """Test classification and prediction using r.learn.ml"""

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

    def test_output_created_labelled_pixels(self):
        """Checks that the output is created"""
        # train model
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.labelled_pixels,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
        )
        self.assertFileExists(filename=self.model_file)

        # create prediction is created
        self.assertModule(
            "r.learn.predict",
            group=self.group,
            load_model=self.model_file,
            output=self.output,
        )
        self.assertRasterExists(self.output, msg="Output was not created")

        # check categories were applied to classification map
        cats_input = gs.parse_command(
            "r.category",
            map=self.labelled_pixels,
            separator=":",
            delimiter=":"
        )
        
        cats_result = gs.parse_command(
            "r.category",
            map=self.output,
            separator=":",
            delimiter=":"
        )

        self.assertEqual(cats_input, cats_result)

    def test_output_created_prediction_points(self):
        """Checks that output is created"""
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_points=self.labelled_points,
            field="value",
            model_name="RandomForestClassifier",
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
            training_points=self.labelled_points,
            field="value",
            model_name="RandomForestClassifier",
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
            model_name="RandomForestClassifier",
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
