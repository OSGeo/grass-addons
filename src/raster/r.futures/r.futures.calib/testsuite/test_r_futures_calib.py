#!/usr/bin/env python3
import os
import filecmp
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPGACalib(TestCase):

    pga_params = dict(
        development_pressure="devpressure",
        predictors=["slope", "lakes_dist_km", "streets_dist_km"],
        n_dev_neighbourhood=15,
        devpot_params="data/potential.csv",
        num_neighbors=4,
        seed_search="random",
        development_pressure_approach="gravity",
        gamma=1.5,
        scaling_factor=1,
        subregions="zipcodes",
        demand="data/demand.csv",
    )

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="lsat7_2002_30@PERMANENT")
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
            ],
        )
        cls.del_temp_region()

    def tearDown(self):
        for each in (
            "data/out_library.txt",
            "data/out_library_subregion.csv",
            "data/out_calib.csv",
            "data/out_calib_subregion.csv",
        ):
            try:
                os.remove(each)
            except OSError:
                pass

    def test_pga_calib_library(self):
        """Test if generated patch library matches the reference"""
        self.assertModule(
            "r.futures.calib",
            flags="l",
            development_start="urban_1987",
            development_end="urban_2002",
            patch_threshold=0,
            subregions="zipcodes",
            patch_sizes="data/out_library.txt",
        )
        self.assertTrue(
            filecmp.cmp("data/out_library.txt", "data/ref_library.txt", shallow=False),
            "Patch libraries differ",
        )

    def test_pga_calib_library_subregions(self):
        """Test if generated patch library matches the reference"""
        self.assertModule(
            "r.futures.calib",
            flags="ls",
            development_start="urban_1987",
            development_end="urban_2002",
            patch_threshold=0,
            subregions="zipcodes",
            patch_sizes="data/out_library_subregion.csv",
            nprocs=8,
        )
        self.assertTrue(
            filecmp.cmp(
                "data/out_library_subregion.csv",
                "data/ref_library_subregion.csv",
                shallow=False,
            ),
            "Patch libraries differ",
        )

    def test_pga_calib_compactness(self):
        """Test if compactness calib file matches the reference"""
        self.assertModule(
            "r.futures.calib",
            development_start="urban_1987",
            development_end="urban_2002",
            patch_threshold=0,
            patch_sizes="data/out_library.txt",
            compactness_mean=[0.1, 0.8],
            compactness_range=[0.1],
            discount_factor=[0.1],
            calibration_results="data/out_calib.csv",
            nprocs=1,
            repeat=2,
            random_seed=1,
            **self.pga_params
        )
        self.assertTrue(
            filecmp.cmp("data/out_calib.csv", "data/ref_calib.csv", shallow=False),
            "Calibration results differ",
        )

    def test_pga_calib_compactness_subregions(self):
        """Test if compactness calib file matches the reference"""
        self.assertModule(
            "r.futures.calib",
            flags="s",
            development_start="urban_1987",
            development_end="urban_2002",
            patch_threshold=0,
            patch_sizes="data/out_library_subregion.csv",
            compactness_mean=[0.1, 0.8],
            compactness_range=[0.1],
            discount_factor=[0.1],
            calibration_results="data/out_calib_subregion.csv",
            nprocs=1,
            repeat=2,
            random_seed=1,
            **self.pga_params
        )
        self.assertTrue(
            filecmp.cmp(
                "data/out_library_subregion.csv",
                "data/ref_library_subregion.csv",
                shallow=False,
            ),
            "Patch libraries differ",
        )
        self.assertTrue(
            filecmp.cmp(
                "data/out_calib_subregion.csv",
                "data/ref_calib_subregion.csv",
                shallow=False,
            ),
            "Calibration results differ",
        )


if __name__ == "__main__":
    test()
