#!/usr/bin/env python3

import os
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPotential(TestCase):

    output = "potential.csv"
    dredge_out = "dredge_out.csv"

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
            expression="urban_2002 = if(ndvi_2002 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )
        cls.runModule(
            "r.mapcalc",
            expression="urban_1987 = if(ndvi_1987 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
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
        cls.runModule(
            "r.mapcalc",
            expression="urban_change = if(urban_2002 == 1, if(urban_1987 == 0, 1, null()), 0)",
        )
        cls.runModule("r.mapcalc", expression="single_level = 1")
        cls.runModule(
            "r.sample.category",
            input="urban_change",
            output="sampling",
            sampled=[
                "zipcodes",
                "single_level",
                "devpressure",
                "slope",
                "lakes_dist_km",
                "streets_dist_km",
            ],
            npoints=[500, 100],
            random_seed=1,
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
                "urban_change",
                "single_level",
            ],
        )
        cls.runModule("g.remove", flags="f", type="vector", name=["sampling"])
        cls.del_temp_region()

    def tearDown(self):
        try:
            os.remove(self.output)
            os.remove(self.dredge_out)
        except OSError:
            pass

    def test_potential_run(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.potential",
            input="sampling",
            columns=["devpressure", "lakes_dist_km", "slope", "streets_dist_km"],
            developed_column="urban_change",
            subregions_column="zipcodes",
            output=self.output,
        )
        with open(self.output, "r") as f:
            i = 0
            for line in f.readlines():
                line = line.strip().split(",")
                self.assertEqual(len(line), 6)
                if i == 0:
                    self.assertEqual(
                        line,
                        [
                            "ID",
                            "Intercept",
                            "devpressure",
                            "lakes_dist_km",
                            "slope",
                            "streets_dist_km",
                        ],
                    )
                i += 1
            self.assertEqual(i, 14)

    def test_potential_run_dredge(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.potential",
            flags="d",
            input="sampling",
            columns=["devpressure", "lakes_dist_km", "slope", "streets_dist_km"],
            developed_column="urban_change",
            subregions_column="zipcodes",
            min_variables=4,
            max_variables=4,
            output=self.output,
        )
        with open(self.output, "r") as f:
            i = 0
            for line in f.readlines():
                line = line.strip().split(",")
                self.assertEqual(len(line), 6)
                if i == 0:
                    self.assertEqual(
                        sorted(line),
                        [
                            "ID",
                            "Intercept",
                            "devpressure",
                            "lakes_dist_km",
                            "slope",
                            "streets_dist_km",
                        ],
                    )
                i += 1
            self.assertEqual(i, 14)

    def test_potential_run_dredge_export(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.potential",
            flags="d",
            input="sampling",
            columns=["devpressure", "lakes_dist_km", "slope", "streets_dist_km"],
            developed_column="urban_change",
            subregions_column="zipcodes",
            min_variables=3,
            max_variables=4,
            nprocs=2,
            fixed_columns=["slope"],
            dredge_output=self.dredge_out,
            output=self.output,
        )
        with open(self.output, "r") as f:
            i = 0
            for line in f.readlines():
                line = line.strip().split(",")
                self.assertEqual(len(line), 5)
                if i == 0:
                    self.assertEqual(
                        line,
                        ["ID", "Intercept", "devpressure", "streets_dist_km", "slope"],
                    )
                i += 1
            self.assertEqual(i, 14)
        with open(self.dredge_out, "r") as f:
            i = 0
            for line in f.readlines():
                line = line.strip().split(",")
                self.assertEqual(len(line), 11)
                if i == 0:
                    self.assertEqual(
                        line,
                        [
                            "ID",
                            "Intercept",
                            "devpressure",
                            "lakes_dist_km",
                            "slope",
                            "streets_dist_km",
                            "df",
                            "logLik",
                            "AIC",
                            "delta",
                            "weight",
                        ],
                    )
                i += 1
            self.assertEqual(i, 5)

    def test_potential_run_single_level(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.potential",
            input="sampling",
            columns=["devpressure", "lakes_dist_km", "slope", "streets_dist_km"],
            developed_column="urban_change",
            subregions_column="single_level",
            output=self.output,
        )
        with open(self.output, "r") as f:
            i = 0
            for line in f.readlines():
                line = line.strip().split(",")
                self.assertEqual(len(line), 6)
                if i == 0:
                    self.assertEqual(
                        line,
                        [
                            "ID",
                            "Intercept",
                            "devpressure",
                            "lakes_dist_km",
                            "slope",
                            "streets_dist_km",
                        ],
                    )
                i += 1
            self.assertEqual(i, 2)


if __name__ == "__main__":
    test()
