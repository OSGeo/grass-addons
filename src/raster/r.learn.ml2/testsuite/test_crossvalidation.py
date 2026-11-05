#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.train cross-validation reporting

AUTHOR(S): the GRASS Development Team

PURPOSE:   Regression tests for the cv > 1 reporting block of r.learn.train:
           fold-label assignment (stratified and grouped splits) and the
           smallest-class guard.

COPYRIGHT: (C) 2026 by the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import csv
import os
import tempfile

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule
from grass.gunittest.main import test


class TestCrossValidation(TestCase):
    """Test the cross-validation fold labelling and class-count guard."""

    # predictor bands from the NC SPM sample dataset
    bands = [
        "lsat7_2002_10@PERMANENT",
        "lsat7_2002_20@PERMANENT",
        "lsat7_2002_30@PERMANENT",
        "lsat7_2002_40@PERMANENT",
        "lsat7_2002_50@PERMANENT",
        "lsat7_2002_70@PERMANENT",
    ]
    classif_map = "landclass96@PERMANENT"

    group = "predictors"
    sample = "cv_sample"
    training = "cv_training_pixels"
    group_ids = "cv_group_ids"

    # save_model is a required option of r.learn.train
    model_file = tempfile.NamedTemporaryFile(suffix=".gz").name

    @classmethod
    def setUpClass(cls):
        """Create an imagery group, labelled training pixels and a group-id map."""
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.classif_map)
        cls.runModule("i.group", group=cls.group, input=cls.bands)
        # Pick 600 random sample locations, then assign synthetic, balanced
        # labels (two classes by row parity) so StratifiedKFold with cv=3 is
        # always valid, independent of the land-cover class frequencies (some
        # landclass96 classes have only a handful of pixels).
        cls.runModule(
            "r.random",
            input=cls.classif_map,
            npoints=600,
            raster=cls.sample,
            seed=1234,
        )
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.training} = if(!isnull({cls.sample}), (row() % 2) + 1, null())",
        )
        # Four spatial groups by column, independent of the row-based class
        # labels, so GroupKFold folds are not contiguous blocks of samples.
        cls.runModule("r.mapcalc", expression=f"{cls.group_ids} = col() % 4")

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[cls.sample, cls.training, cls.group_ids],
        )
        cls.runModule("g.remove", flags="f", type="group", name=cls.group)

    def tearDown(self):
        try:
            os.remove(self.model_file)
        except FileNotFoundError:
            pass

    @staticmethod
    def _read_folds(preds_file):
        """Return the fold column of a preds_file as a list of ints."""
        with open(preds_file, newline="") as fh:
            return [int(row["fold"]) for row in csv.DictReader(fh)]

    def _remove_preds(self, preds_file):
        for name in (preds_file, preds_file + "t"):  # .csv and its .csvt sidecar
            try:
                os.remove(name)
            except FileNotFoundError:
                pass

    def test_fold_labels_stratified(self):
        """Every sample gets a valid fold id (StratifiedKFold path).

        Guards the fold-labelling fix: predictions come back in the original
        sample order, so fold ids must land in {0 .. cv-1} with none left as
        the -1 "uncovered" sentinel.
        """
        cv = 3
        preds_file = tempfile.NamedTemporaryFile(suffix=".csv").name
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.training,
            model_name="RandomForestClassifier",
            n_estimators=25,
            cv=cv,
            preds_file=preds_file,
            save_model=self.model_file,
        )
        self.assertFileExists(filename=preds_file)
        folds = self._read_folds(preds_file)
        self._remove_preds(preds_file)

        self.assertTrue(folds, msg="preds_file has no rows")
        self.assertEqual(
            set(folds),
            set(range(cv)),
            msg="fold column must contain exactly folds 0..cv-1 (no -1 sentinel)",
        )

    def test_fold_labels_grouped(self):
        """The grouped (GroupKFold) path runs and labels folds correctly.

        The pre-fix code called outer.split(X, y) without the group ids while
        building the fold column, which raised for GroupKFold. This asserts the
        grouped run now succeeds and produces well-formed fold ids.
        """
        cv = 3
        preds_file = tempfile.NamedTemporaryFile(suffix=".csv").name
        self.assertModule(
            "r.learn.train",
            group=self.group,
            training_map=self.training,
            group_raster=self.group_ids,
            model_name="RandomForestClassifier",
            n_estimators=25,
            cv=cv,
            preds_file=preds_file,
            save_model=self.model_file,
        )
        self.assertFileExists(filename=preds_file)
        folds = self._read_folds(preds_file)
        self._remove_preds(preds_file)

        self.assertTrue(folds, msg="preds_file has no rows")
        self.assertTrue(
            set(folds).issubset(set(range(cv))),
            msg="grouped fold ids must stay within 0..cv-1 (no -1 sentinel)",
        )

    def test_small_class_fails(self):
        """cv larger than the smallest class aborts with a clear error.

        Guards the class-count fix: the old np.histogram check merged classes
        and never fired, so an undersized class only failed later with an
        opaque scikit-learn error.
        """
        tiny = "cv_tiny_training"
        # Row 1 only: 8 pixels of class 1 and 2 pixels of class 2.
        self.runModule(
            "r.mapcalc",
            expression=f"{tiny} = if(row() == 1, if(col() <= 8, 1, "
            f"if(col() <= 10, 2, null())), null())",
            overwrite=True,
        )
        try:
            # cv = 3 > 2 samples in the smallest class -> fatal.
            module = SimpleModule(
                "r.learn.train",
                group=self.group,
                training_map=tiny,
                model_name="RandomForestClassifier",
                n_estimators=25,
                cv=3,
                save_model=self.model_file,
            )
            self.assertModuleFail(module)
            # Confirm it aborts on the class-count guard, not some other error.
            self.assertIn("smallest class", str(module.outputs.stderr))
        finally:
            self.runModule("g.remove", flags="f", type="raster", name=tiny)


if __name__ == "__main__":
    test()
