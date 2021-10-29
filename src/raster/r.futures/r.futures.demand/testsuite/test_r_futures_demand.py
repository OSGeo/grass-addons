#!/usr/bin/env python3

import os
import filecmp
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestPGA(TestCase):

    output = "output_demand.csv"
    output_plot = "output_plot.pdf"
    reference_demand = "data/demand.csv"
    reference_demand_2 = "data/demand_2.csv"

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
        cls.runModule(
            "r.mapcalc",
            expression="urban_2005 = if(ndvi_2002 <= 0.15 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )
        cls.runModule(
            "r.mapcalc",
            expression="urban_2006 = if(ndvi_2002 <= 0.18 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                "ndvi_2002",
                "ndvi_1987",
                "urban_1987",
                "urban_2002",
                "urban_2005",
                "urban_2006",
            ],
        )
        cls.del_temp_region()

    def tearDown(self):
        try:
            os.remove(self.output)
            os.remove(self.output_plot)
        except OSError:
            pass

    def test_demand_run(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.demand",
            development="urban_1987,urban_2002,urban_2005,urban_2006",
            subregions="zipcodes",
            observed_population="data/observed_population.csv",
            projected_population="data/projected_population.csv",
            simulation_times=list(range(2006, 2011)),
            method=["linear", "logarithmic", "exponential"],
            plot=self.output_plot,
            demand=self.output,
        )
        self.assertTrue(os.path.exists(self.output_plot))
        self.assertTrue(
            filecmp.cmp(self.output, self.reference_demand, shallow=False),
            "Demand results differ",
        )

    # def test_demand_run_inverse_relation(self):
    #     """Test case when population is decreasing"""
    #     self.assertModule('r.futures.demand',
    #                       development='urban_1987,urban_2002,urban_2005,urban_2006',
    #                       subregions='zipcodes',
    #                       observed_population='data/observed_population_2.csv',
    #                       projected_population='data/projected_population_2.csv',
    #                       simulation_times=list(range(2006, 2011)),
    #                       method=['linear', 'logarithmic', 'exponential'],
    #                       plot=self.output_plot,
    #                       demand=self.output)
    #     self.assertTrue(os.path.exists(self.output_plot))
    #     self.assertTrue(filecmp.cmp(self.output, self.reference_demand_2, shallow=False),
    #                     "Demand results differ")


if __name__ == "__main__":
    test()
