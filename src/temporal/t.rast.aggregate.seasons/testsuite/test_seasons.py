"""Test for t.rast.seasons
(C) 2023 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
@author Luca Delucchi
"""

import grass.temporal as tgis
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

class TestClimatologies(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        tgis.init(True)  # Raise on error instead of exit(1)
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=80, w=0, e=120, b=0, t=50, res=10, res3=10)

        cls.runModule("r.mapcalc", expression="a_1 = 5", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = 10", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = 15", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = 20", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_5 = 25", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_6 = 30", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_7 = 35", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_8 = 40", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_9 = 45", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_10 = 50", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_11 = 55", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_12 = 60", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_1 = 5", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_2 = 10", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_3 = 15", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_4 = 20", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_5 = 25", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_6 = 30", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_7 = 35", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_8 = 40", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_9 = 45", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_10 = 50", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_11 = 55", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_12 = 60", overwrite=True)

        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output="monthly",
            title="Monthly test",
            description="Monthly test",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="monthly",
            maps="a_1,a_2,a_3,a_4,a_5,a_6,a_7,a_8,a_9,a_10,a_11,a_12",
            start="2001-01-01",
            increment="1 month",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="monthly",
            maps="b_1,b_2,b_3,b_4,b_5,b_6,b_7,b_8,b_9,b_10,b_11,b_12",
            start="2002-01-01",
            increment="1 month",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the time series"""
        cls.runModule("t.remove", flags="rf", type="strds", inputs="monthly")

    def test_no_years(self):
        """Test on all years"""
        self.assertModule(
            "t.rast.aggregate.seasons",
            input="monthly",
            output="monthly_seasons",
            basename="seasons",
            overwrite=True,
            verbose=True,
        )
        out = tgis.open_old_stds("monthly_seasons", type="strds")
        self.assertEqual(out.metadata.get_number_of_maps(), 7)

    def test_one_year(self):
        """Test just one year"""
        self.assertModule(
            "t.rast.aggregate.seasons",
            input="monthly",
            basename="oneseason",
            years=2002,
            overwrite=True,
            verbose=True,
        )
        out = tgis.open_old_stds("oneseason_2002", type="strds")
        self.assertEqual(out.metadata.get_number_of_maps(), 3)

    def test_error_missing_basename(self):
        """Test if basename is missing"""
        self.assertModuleFail(
            "t.rast.aggregate.seasons",
            input="monthly",
        )

if __name__ == '__main__':
    test()
