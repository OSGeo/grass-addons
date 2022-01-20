"""Test v.to.rast.multi

(C) 2022 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Stefan Blumentrath
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule


class TestVToRastMulti(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        cls.use_temp_region()
        cls.runModule("g.region", raster="boundary_county_500m")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.runModule("g.remove", flags="rf", type="raster", pattern="vtorastmulti_*")
        cls.del_temp_region()

    def test_manual_example(self):

        manual_example_run = SimpleModule(
            "v.to.rast.multi",
            verbose=True,
            input="census_wake2000",
            type="area",
            output="vtorastmulti",
            attribute_columns="RINGS_OK,TRACT",
            label_columns="ID,TRACTID",
            memory=3000,
            ndigits=[0, 4],
            separator=",",
        )
        self.assertModule(manual_example_run)

        values = """n=8888
null_cells=1113694
cells=1122582
min=5010000
max=5440200
range=430200
mean=5349800.34552205
mean_of_abs=5349800.34552205
stddev=66121.0453170682
variance=4371992633.82178
coeff_var=1.23595351315145
sum=47549025471"""
        self.assertRasterFitsUnivar(
            raster="vtorastmulti_TRACT", reference=values, precision=1
        )

        values = """n=8888
null_cells=1113694
cells=1122582
min=1
max=1
range=0
mean=1
mean_of_abs=1
stddev=0
variance=0
coeff_var=0
sum=8888"""
        self.assertRasterFitsUnivar(
            raster="vtorastmulti_RINGS_OK", reference=values, precision=1
        )


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
