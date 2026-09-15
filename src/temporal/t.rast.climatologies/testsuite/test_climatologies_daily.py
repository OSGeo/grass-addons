"""Test t.rast.climatologies
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
        cls.runModule("r.mapcalc", expression="b_1 = 5", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_2 = 10", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_3 = 15", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_4 = 20", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_5 = 25", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_6 = 30", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_7 = 35", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_8 = 40", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_9 = 45", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_1 = 5", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_2 = 10", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_3 = 15", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_4 = 20", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_5 = 25", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_6 = 30", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_7 = 35", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_8 = 40", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_9 = 45", overwrite=True)

        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output="daily",
            title="Daily test",
            description="Daily test",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="daily",
            maps="a_1,a_2,a_3,a_4,a_5,a_6,a_7,a_8,a_9",
            start="2001-01-01",
            increment="1 day",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="daily",
            maps="b_1,b_2,b_3,b_4,b_5,b_6,b_7,b_8,b_9",
            start="2002-01-01",
            increment="1 day",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="daily",
            maps="c_1,c_2,c_3,c_4,c_5,c_6,c_7,c_8,c_9",
            start="2003-01-01",
            increment="1 day",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the time series"""
        cls.runModule("t.remove", flags="fd", type="strds", inputs="daily")

    def test_1(self):
        """Test average data"""
        self.assertModule(
            "t.rast.climatologies",
            input="daily",
            output="daily_clima",
            method="average",
            basename="daily_avg",
            granularity="day",
            overwrite=True,
            verbose=True,
        )
        out = tgis.open_old_stds("daily_clima", type="strds")
        self.assertEqual(out.metadata.get_number_of_maps(), 9)
        self.assertEqual(out.metadata.get_min_min(), 5)
        self.assertEqual(out.metadata.get_max_max(), 45)
        self.runModule("t.remove", flags="df", type="strds", inputs="daily_clima")

    def test_noout(self):
        """Don't create output strds"""
        self.assertModule(
            "t.rast.climatologies",
            input="daily",
            flags=["s"],
            method="average",
            basename="daily_avg",
            granularity="day",
            overwrite=True,
            verbose=True,
        )
        self.assertRasterExists("daily_avg_01_01")
        self.assertRasterExists("daily_avg_01_09")
        self.assertRasterDoesNotExist("daily_avg_01_10")
        self.runModule("g.remove", flags="f", type="raster", pattern="daily_avg_*")


if __name__ == "__main__":
    test()
