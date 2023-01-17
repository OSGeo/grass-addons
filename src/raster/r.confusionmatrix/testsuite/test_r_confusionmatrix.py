"""
Name:       r.confusionmatrix test
Purpose:    Tests r.confusionmatrix input parsing.
            Uses NC full sample data set.
Author:     Anika Weinmann
Copyright:  (C) 2020-2023 Anika Weinmann, mundialis, and the GRASS Development Team
Licence:    This program is free software under the GNU General Public
            License (>=v2). Read the file COPYING that comes with GRASS
            for details.
"""

import os

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class Testconfusionmatrix(TestCase):
    classification = "landuse96_28m"
    classification_oneclass = "landuse96_28m_class1only"
    raster_ref = "landclass96"
    raster_ref_oneclass = "landclass96_class1only"
    output_csv = "output_confusionmatrix.csv"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region and generated data"""
        cls.use_temp_region()
        # set region to classification
        cls.runModule("g.region", raster=cls.classification)
        cls.runModule(
            "r.mapcalc",
            expression="%s = if(%s==1,1, null())"
            % (cls.raster_ref_oneclass, cls.raster_ref),
        )
        cls.runModule("r.mapcalc", expression="%s = 1" % (cls.classification_oneclass))

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region and generated data"""
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            type="raster",
            name="%s,%s" % (cls.raster_ref_oneclass, cls.classification_oneclass),
            flags="f",
        )

    def tearDown(self):
        """Remove the outputs created

        This is executed after each test run.
        """
        if os.path.isfile(self.output_csv):
            os.remove(self.output_csv)

    def test_confusionmatrix_with_raster_reference(self):
        """Test confusionmatrix with raster reference"""
        self.assertModule(
            "r.confusionmatrix",
            classification=self.classification,
            raster_reference=self.raster_ref,
            flags="m",
            csvfile=self.output_csv,
        )
        # check to see if output file exists
        self.assertFileExists(self.output_csv, msg="Output file does not exist")
        # check if the output file is equal to the reference file
        self.assertFilesEqualMd5(
            self.output_csv,
            "data/confusionmatrix_raster_matrix.csv",
            msg="Output file is not equal to reference file",
        )

    def test_confusionmatrix_with_singleclass(self):
        """Test confusionmatrix with a single class reference and classification"""
        r_confusion = SimpleModule(
            "r.confusionmatrix",
            classification=self.classification_oneclass,
            raster_reference=self.raster_ref_oneclass,
            flags="m",
            csvfile=self.output_csv,
        )
        self.assertModule(r_confusion)
        # check to see if output file exists
        self.assertFileExists(self.output_csv, msg="Output file does not exist")
        # check if the output file is equal to the reference file
        self.assertFilesEqualMd5(
            self.output_csv,
            "data/confusionmatrix_raster_matrix_oneclass.csv",
            msg="Output file is not equal to reference file",
        )
        # test that the warning is shown
        stderr = r_confusion.outputs.stderr
        self.assertIn("Only one class in reference dataset.", stderr)


if __name__ == "__main__":
    test()
