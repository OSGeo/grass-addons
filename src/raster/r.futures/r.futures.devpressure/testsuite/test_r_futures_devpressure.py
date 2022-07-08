#!/usr/bin/env python3

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestDevpressure(TestCase):

    output = "devpressure_output"
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
            expression="urban_2002 = if(ndvi_2002 <= 0.1 && isnull(lakes), 1, if(isnull(lakes), 0, null()))",
        )

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=["ndvi_2002", "urban_2002", cls.result],
        )
        cls.del_temp_region()

    def tearDown(self):
        self.runModule("g.remove", flags="f", type="raster", name=self.output)

    def test_devpressure_run(self):
        """Test if results is in expected limits"""
        self.assertModule(
            "r.futures.devpressure",
            input="urban_2002",
            output=self.output,
            method="gravity",
            size=15,
            flags="n",
            nprocs=2,
        )
        self.assertRastersNoDifference(
            actual=self.output, reference=self.result, precision=1e-6
        )


if __name__ == "__main__":
    test()
