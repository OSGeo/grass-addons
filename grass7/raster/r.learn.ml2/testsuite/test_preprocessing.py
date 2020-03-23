#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.train

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.train

COPYRIGHT: (C) 2020 by Steven Pawley and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""
import tempfile
import os

import grass.script as gs

import joblib
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPreprocessing(TestCase):
    """Test preprocessing options using r.learn.ml"""

    band1 = "lsat7_2002_10@PERMANENT"
    band2 = "lsat7_2002_20@PERMANENT"
    band3 = "lsat7_2002_30@PERMANENT"
    band4 = "lsat7_2002_40@PERMANENT"
    band5 = "lsat7_2002_50@PERMANENT"
    band7 = "lsat7_2002_70@PERMANENT"
    geology = "geology_30m@PERMANENT"
    classif_map = "landclass96@PERMANENT"

    output = "classification_result"
    model_file = tempfile.NamedTemporaryFile(suffix=".gz").name
    group = "predictors"
    labelled_pixels = "training_pixels"

    @classmethod
    def setUpClass(cls):
        """Setup that is required for all tests
        
        Uses a temporary region for testing and creates an imagery group and randomly samples a
        categorical map to use as training pixels
        """
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.classif_map)
        cls.runModule(
            "i.group",
            group=cls.group,
            input=[
                cls.band1,
                cls.band2,
                cls.band3,
                cls.band4,
                cls.band5,
                cls.band7,
                cls.geology,
            ],
        )
        cls.runModule(
            "r.random",
            input=cls.classif_map,
            npoints=1000,
            raster=cls.labelled_pixels,
            seed=1234,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        cls.del_temp_region()
        cls.runModule("g.remove", flags="f", type="raster", name=cls.labelled_pixels)
        cls.runModule("g.remove", flags="f", type="group", name=cls.group)

    def tearDown(self):
        """Remove the output created from the tests
        (reuse the same name for all the test functions)"""
        self.runModule("g.remove", flags="f", type="raster", name=[self.output])

        try:
            os.remove(self.model_file)
        except FileNotFoundError:
            pass

    def test_onehot(self):
        """Checks that onehot encoding execution passes"""
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.labelled_pixels,
            model_name="RandomForestClassifier",
            n_estimators=100,
            category_maps=self.geology,
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

        estimator, y, class_labels = joblib.load(self.model_file)
        trans = estimator.named_steps['preprocessing'].transformers[0]
        self.assertIsInstance(trans[1], OneHotEncoder)
        estimator = None

    def test_standardization(self):
        """Checks that standardization execution passes"""
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.labelled_pixels,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
            flags="s",
        )
        self.assertFileExists(filename=self.model_file)
        self.assertModule(
            "r.learn.predict",
            group=self.group,
            load_model=self.model_file,
            output=self.output,
        )
        self.assertRasterExists(self.output, msg="Output was not created")

        estimator, y, class_labels = joblib.load(self.model_file)
        trans = estimator.named_steps['preprocessing'].transformers[0]
        self.assertIsInstance(trans[1], StandardScaler)
        estimator = None

    def test_ohe_standardization(self):
        """Checks that standardization execution passes"""
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.labelled_pixels,
            model_name="RandomForestClassifier",
            n_estimators=100,
            save_model=self.model_file,
            category_maps=self.geology,
            flags="s",
        )
        self.assertFileExists(filename=self.model_file)
        self.assertModule(
            "r.learn.predict",
            group=self.group,
            load_model=self.model_file,
            output=self.output,
        )
        self.assertRasterExists(self.output, msg="Output was not created")

        estimator, y, class_labels = joblib.load(self.model_file)
        ohe = estimator.named_steps['preprocessing'].transformers[0]
        scaler = estimator.named_steps['preprocessing'].transformers[1]
        self.assertIsInstance(ohe[1], OneHotEncoder)
        self.assertIsInstance(scaler[1], StandardScaler)
        estimator = None

if __name__ == "__main__":
    test()
