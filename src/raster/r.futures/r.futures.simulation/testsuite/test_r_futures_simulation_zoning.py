#!/usr/bin/env python3

"""Tests for zoning parameters in r.futures.simulation."""

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestZoning(TestCase):
    output = "pga_output"
    result_baseline = "result"
    result_predefined = "result_zoning_predefined"
    result_stringency = "result_zoning_stringency"
    result_custom = "result_zoning_custom"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", raster="lsat7_2002_30@PERMANENT")
        # Unpack reference rasters
        cls.runModule("r.unpack", input="data/result.pack", output=cls.result_baseline)
        cls.runModule(
            "r.unpack",
            input="data/result_zoning_predefined.pack",
            output=cls.result_predefined,
        )
        cls.runModule(
            "r.unpack",
            input="data/result_zoning_stringency.pack",
            output=cls.result_stringency,
        )
        cls.runModule(
            "r.unpack",
            input="data/result_zoning_custom.pack",
            output=cls.result_custom,
        )
        # NDVI and urban classification
        cls.runModule(
            "r.mapcalc",
            expression=(
                "ndvi_2002 = double(lsat7_2002_40@PERMANENT"
                " - lsat7_2002_30@PERMANENT)"
                " / double(lsat7_2002_40@PERMANENT"
                " + lsat7_2002_30@PERMANENT)"
            ),
        )
        cls.runModule(
            "r.mapcalc",
            expression=(
                "ndvi_1987 = double(lsat5_1987_40@landsat"
                " - lsat5_1987_30@landsat)"
                " / double(lsat5_1987_40@landsat"
                " + lsat5_1987_30@landsat)"
            ),
        )
        cls.runModule(
            "r.mapcalc",
            expression=(
                "urban_1987 = if(ndvi_1987 <= 0.1 && isnull(lakes),"
                " 1, if(isnull(lakes), 0, null()))"
            ),
        )
        cls.runModule(
            "r.mapcalc",
            expression=(
                "urban_2002 = if(ndvi_2002 <= 0.1 && isnull(lakes),"
                " 1, if(isnull(lakes), 0, null()))"
            ),
        )
        # Predictors
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
        # Zoning rasters
        # Predefined zone IDs mapped from zipcodes
        cls.runModule(
            "r.mapcalc",
            expression=(
                "zoning_predefined = if(zipcodes==27511, 100,"
                " if(zipcodes==27513, 101,"
                " if(zipcodes==27518, 110,"
                " if(zipcodes==27529, 120,"
                " if(zipcodes==27539, 130,"
                " if(zipcodes==27601, 200,"
                " if(zipcodes==27603, 201,"
                " if(zipcodes==27604, 202,"
                " if(zipcodes==27605, 300,"
                " if(zipcodes==27606, 301,"
                " if(zipcodes==27607, 100,"
                " if(zipcodes==27608, 110,"
                " if(zipcodes==27610, 130,"
                " null())))))))))))))"
            ),
        )
        # Custom 3-zone map for custom effects test
        cls.runModule(
            "r.mapcalc",
            expression=(
                "zoning_custom = if(isnull(zipcodes), null(),"
                " if(zipcodes <= 27518, 1,"
                " if(zipcodes <= 27604, 2, 3)))"
            ),
        )
        # All-zero zoning (no effect) for baseline comparison
        cls.runModule(
            "r.mapcalc",
            expression=("zoning_null = if(isnull(zipcodes), null(), 0)"),
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
                "zoning_predefined",
                "zoning_custom",
                "zoning_null",
                cls.result_baseline,
                cls.result_predefined,
                cls.result_stringency,
                cls.result_custom,
            ],
        )
        cls.del_temp_region()

    def tearDown(self):
        self.runModule("g.remove", flags="f", type="raster", name=self.output)

    def _run_simulation(self, **extra_params):
        """Run r.futures.simulation with base parameters plus extras."""
        params = dict(
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
        params.update(extra_params)
        self.assertModule("r.futures.simulation", **params)

    def test_zoning_predefined(self):
        """Test zoning with predefined zone IDs and default effects"""
        self._run_simulation(zoning="zoning_predefined")
        self.assertRastersNoDifference(
            actual=self.output,
            reference=self.result_predefined,
            precision=1e-6,
        )

    def test_zoning_stringency_only(self):
        """Test zoning with predefined effects and regional stringency"""
        self._run_simulation(
            zoning="zoning_predefined",
            zoning_effects="data/zoning_effects_stringency.csv",
        )
        self.assertRastersNoDifference(
            actual=self.output,
            reference=self.result_stringency,
            precision=1e-6,
        )

    def test_zoning_custom_effects(self):
        """Test zoning with custom zone IDs and effects per region"""
        self._run_simulation(
            zoning="zoning_custom",
            zoning_effects="data/zoning_effects_custom.csv",
        )
        self.assertRastersNoDifference(
            actual=self.output,
            reference=self.result_custom,
            precision=1e-6,
        )

    def test_zoning_null_matches_baseline(self):
        """Test that all-zero zoning (no effect) matches baseline output"""
        self._run_simulation(zoning="zoning_null")
        self.assertRastersNoDifference(
            actual=self.output,
            reference=self.result_baseline,
            precision=1e-6,
        )

    def test_zoning_effects_without_zoning_fails(self):
        """Test that providing zoning_effects without zoning raster fails"""
        self.assertModuleFail(
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
            zoning_effects="data/zoning_effects_stringency.csv",
            output=self.output,
        )


if __name__ == "__main__":
    test()
