"""Test i.landsat.qa

(C) 2021 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Stefan Blumentrath

Using examples from the manual
i.landsat.qa --overwrite --verbose cloud="Medium,High" \
    dataset="landsat_ot_c2_l2" \
    output=./Cloud_Mask_rules.txt

# Create a water mask (only available for collection 2):
i.landsat.qa --overwrite --verbose water="Yes" \
    dataset="landsat_ot_c2_l2" \
    output=./Water_Mask_rules.txt
"""

import os
from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule


class TestLandsatQA(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary output"""
        os.remove("Cloud_Mask_rules.txt")
        os.remove("Water_Mask_rules.txt")

    def test_cloud_mask(self):

        cloud_mask = SimpleModule(
            "i.landsat.qa",
            cloud_confidence=["Medium", "High"],
            dataset="landsat_ot_c2_l2",
            output="Cloud_Mask_rules.txt",
            verbose=True,
        )
        self.assertModule(cloud_mask)

    def test_water_mask(self):

        water_mask = SimpleModule(
            "i.landsat.qa",
            water="Yes",
            dataset="landsat_ot_c2_l2",
            output="Water_Mask_rules.txt",
            verbose=True,
        )
        self.assertModule(water_mask)


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
