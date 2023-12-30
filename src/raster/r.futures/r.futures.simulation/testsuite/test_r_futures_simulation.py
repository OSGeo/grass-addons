#!/usr/bin/env python3

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPGA(TestCase):

    output = "pga_output"
    result = "result"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="lsat7_2002_30@PERMANENT")
        cls.runModule("r.unpack", input="data/result.pack", output=cls.result)
        cls.runModule(
            "r.mapcalc",
            expression="ndvi_2002 = double(lsat7_2002_40@PERMANENT - lsat7_2002_30@PERMANENT) / double(lsat7_2002_40@PERMANENT + lsat7_2002_30@PERMANENT)",
        )
        cls.runModule(
            "r.mapcalc",
            expression="ndvi_1987 = double(lsat5_1987_40@landsat - lsat5_1987_30@landsat) / double(lsat5_1987_40@landsat + lsat5_1987_30@landsat)",
        )
        cls.runModule(
            "r.mapcalc",
            expression="urban_1987 = if(ndvi_1987 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )
        cls.runModule(
            "r.mapcalc",
            expression="urban_2002 = if(ndvi_2002 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )
        cls.runModule("r.slope.aspect", elevation="elevation", slope="slope")
        cls.runModule("r.grow.distance", input="lakes", distance="lakes_dist")
        cls.runModule("r.mapcalc", expression="lakes_dist_km = lakes_dist/1000.")
        cls.runModule("v.to.rast", input="streets_wake", output="streets", use="val")
        cls.runModule("r.grow.distance", input="streets", distance="streets_dist")
        cls.runModule("r.mapcalc", expression="streets_dist_km = streets_dist/1000.")
        cls.runModule(
            "r.futures.devpressure",
            input="urban_2002",
            output="devpressure",
            method="gravity",
            size=15,
            flags="n",
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                "slope",
                "lakes_dist",
                "lakes_dist_km",
                "streets",
                "streets_dist",
                "streets_dist_km",
                "devpressure",
                "ndvi_2002",
                "ndvi_1987",
                "urban_1987",
                "urban_2002",
                cls.result,
            ],
        )
        cls.del_temp_region()

    def tearDown(self):
        self.runModule("g.remove", flags="f", type="raster", name=self.output)

    def test_pga_run(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.simulation",
            developed="urban_2002",
            development_pressure="devpressure",
            compactness_mean=0.4,
            compactness_range=0.05,
            discount_factor=0.1,
            patch_sizes="data/patches.txt",
            predictors=["slope", "lakes_dist_km", "streets_dist_km"],
            n_dev_neighbourhood=15,
            devpot_params="data/potential.csv",
            random_seed=1,
            num_neighbors=4,
            seed_search="random",
            development_pressure_approach="gravity",
            gamma=1.5,
            scaling_factor=1,
            subregions="zipcodes",
            demand="data/demand.csv",
            output=self.output,
        )
        self.assertRastersNoDifference(
            actual=self.output, reference=self.result, precision=1e-6
        )

    def test_pga_run_patch_library_multiple_columns(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.simulation",
            developed="urban_2002",
            development_pressure="devpressure",
            compactness_mean=0.4,
            compactness_range=0.05,
            discount_factor=0.1,
            patch_sizes="data/patches.csv",
            predictors=["slope", "lakes_dist_km", "streets_dist_km"],
            n_dev_neighbourhood=15,
            devpot_params="data/potential.csv",
            random_seed=1,
            num_neighbors=4,
            seed_search="random",
            development_pressure_approach="gravity",
            gamma=1.5,
            scaling_factor=1,
            subregions="zipcodes",
            demand="data/demand.csv",
            output=self.output,
        )
        self.assertRastersNoDifference(
            actual=self.output, reference=self.result, precision=1e-6
        )


if __name__ == "__main__":
    test()
