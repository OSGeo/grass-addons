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

from grass.gunittest.case import TestCase


class TestProbabilties(TestCase):
    """Test class probability prediction using r.learn.ml"""

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

    # raster map created as output during test
    output = "classification_result"
    output_probs = ["classification_result_" + str(i) for i in range(1, 8)]

    # files created during test
    model_file = tempfile.NamedTemporaryFile(suffix=".gz").name

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

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region (and anything else we created)"""
        cls.del_temp_region()
        cls.runModule("g.remove", flags="f", type="raster", name=cls.labelled_pixels)
        cls.runModule("g.remove", flags="f", type="group", name=cls.group)

    def tearDown(self):
        """Remove the output created from the tests
        (reuse the same name for all the test functions)"""
        self.runModule("g.remove", flags="f", type="raster", name=self.output_probs)
        os.remove(self.model_file)

    def test_probabilities(self):
        """Checks that class probabilities are produced"""
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
            flags="pz"
        )

        self.assertRasterExists(self.output_probs[0], msg="Output was not created")
        self.assertRasterExists(self.output_probs[1], msg="Output was not created")
        self.assertRasterExists(self.output_probs[2], msg="Output was not created")
        self.assertRasterExists(self.output_probs[3], msg="Output was not created")
        self.assertRasterExists(self.output_probs[4], msg="Output was not created")
        self.assertRasterExists(self.output_probs[5], msg="Output was not created")
        self.assertRasterExists(self.output_probs[6], msg="Output was not created")
