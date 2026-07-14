"""Tests for t.rast.vi
(C) 2026 by the GRASS Development Team
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
        tgis.init(raise_fatal_error=True)
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=80, w=0, e=120, b=0, t=50, res=10, res3=10)

        cls.runModule("r.mapcalc", expression="a_1 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_5 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_6 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_7 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_8 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_9 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_10 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_11 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_12 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_1 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_2 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_3 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_4 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_5 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_6 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_7 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_8 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_9 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_10 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_11 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="b_12 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_1 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_2 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_3 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_4 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_5 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_6 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_7 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_8 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_9 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_10 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_11 = rand(1,256)", overwrite=True)
        cls.runModule("r.mapcalc", expression="c_12 = rand(1,256)", overwrite=True)

        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output="red_monthly",
            title="Monthly test RED data",
            description="Monthly test RED data",
            overwrite=True,
        )
        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output="nir_monthly",
            title="Monthly test NIR data",
            description="Monthly test NIR data",
            overwrite=True,
        )
        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output="blue_monthly",
            title="Monthly test BLUE data",
            description="Monthly test BLUE data",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="red_monthly",
            maps="a_1,a_2,a_3,a_4,a_5,a_6,a_7,a_8,a_9,a_10,a_11,a_12",
            start="2001-01-01",
            increment="1 month",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="nir_monthly",
            maps="b_1,b_2,b_3,b_4,b_5,b_6,b_7,b_8,b_9,b_10,b_11,b_12",
            start="2001-01-01",
            increment="1 month",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input="blue_monthly",
            maps="c_1,c_2,c_3,c_4,c_5,c_6,c_7,c_8,c_9,c_10,c_11,c_12",
            start="2001-01-01",
            increment="1 month",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the time series"""
        cls.runModule(
            "t.remove", flags="rf", type="strds", inputs="red_monthly,nir_monthly"
        )

    def test_ndvi(self):
        self.runModule(
            "t.rast.vi",
            red="red_monthly",
            nir="nir_monthly",
            output="ndvi_monthly",
            viname="ndvi",
            prefix="ndvimonthly",
            overwrite=True,
        )
        print("Check if the output raster map exists")
        self.assertRasterExists("ndvimonthly_2001_01_01_00_00_ndvi")

    def test_evi(self):
        self.runModule(
            "t.rast.vi",
            red="red_monthly",
            nir="nir_monthly",
            blue="blue_monthly",
            output="evi_monthly",
            viname="evi",
            prefix="evimonthly",
            overwrite=True,
        )
        print("Check if the output raster map exists")
        self.assertRasterExists("evimonthly_2001_01_01_00_00_evi")

    def test_missing_output(self):
        self.assertModuleFail(
            "t.rast.vi",
            red="red_monthly",
            nir="nir_monthly",
            viname="ndvi",
            prefix="ndvimonthly",
            overwrite=True,
        )

    def test_missing_band(self):
        self.assertModuleFail(
            "t.rast.vi",
            red="red_monthly",
            nir="nir_monthly",
            blue="blue_monthly",
            output="gari_monthly",
            viname="gari",
            prefix="garimonthly",
            overwrite=True,
        )


if __name__ == "__main__":
    test()
