"""
Name:       r.confusionmatrix test
Purpose:    Tests r.confusionmatrix input parsing.
            Uses NC full sample data set.
Author:     Anika Bettge
Copyright:  (C) 2020 Anika Bettge, mundialis, and the GRASS Development Team
Licence:    This program is free software under the GNU General Public
            License (>=v2). Read the file COPYING that comes with GRASS
            for details.
"""

import os

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

class Testconfusionmatrix(TestCase):
    classification = 'landuse96_28m'
    raster_ref = 'landclass96'
    output_csv = 'output_confusionmatrix.csv'

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region and generated data"""
        cls.use_temp_region()
        # set region to classification
        cls.runModule('g.region', raster=cls.classification)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region and generated data"""
        cls.del_temp_region()

    def tearDown(self):
        """Remove the outputs created

        This is executed after each test run.
        """
        if os.path.isfile(self.output_csv):
            os.remove(self.output_csv)

    def test_confusionmatrix_with_raster_reference(self):
        """Test confusionmatrix with raster reference"""
        self.assertModule('r.confusionmatrix',
            classification=self.classification,
            raster_reference=self.raster_ref,
            flags='m',
            csvfile=self.output_csv)
        # check to see if output file exists
        self.assertFileExists(self.output_csv,
                               msg='Output file does not exist')
        # check if the output file is equal to the reference file
        self.assertFilesEqualMd5(self.output_csv,
                               'data/confusionmatrix_raster_matrix.csv',
                               msg='Output file is not equal to reference file')



if __name__ == '__main__':
    test()
