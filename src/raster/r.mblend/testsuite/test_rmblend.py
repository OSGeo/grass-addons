from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestRMblend(TestCase):

    low_res = "low_res"
    high_res_1 = "high_res_1"
    high_res_2 = "high_res_2"
    result_1 = "result_1"
    result_2 = "result_2"

    @classmethod
    def setUpClass(cls):

        cls.runModule("g.region", s=0, n=100, w=0, e=100, res=2)
        cls.runModule("r.mapcalc", expression="{} = 2".format(cls.low_res))
        cls.runModule("g.region", s=0, n=100, w=0, e=60, res=1)
        cls.runModule("r.mapcalc", expression="{} = 1".format(cls.high_res_1))
        cls.runModule("g.region", s=20, n=80, w=30, e=70, res=1)
        cls.runModule("r.mapcalc", expression="{} = 1".format(cls.high_res_2))
        cls.runModule("g.region", s=0, n=100, w=0, e=100, res=1)

    @classmethod
    def tearDownClass(cls):

        cls.runModule(
            "g.remove",
            type="raster",
            flags="f",
            name=[cls.high_res_1, cls.high_res_2, cls.low_res],
        )

    def tearDown(self):

        self.runModule(
            "g.remove",
            type="raster",
            flags="f",
            name=[self.result_1, self.result_2],
        )

    def test_module_basic(self):

        self.assertModule(
            "r.mblend",
            high=self.high_res_1,
            low=self.low_res,
            output=self.result_1,
        )
        self.assertRasterExists(name=self.result_1)

    def test_results(self):

        self.assertModule(
            "r.mblend",
            high=self.high_res_1,
            low=self.low_res,
            output=self.result_1,
            inter_points=100,
        )
        self.assertRasterExists(name=self.result_1)
        values = "min=1\nmax=2\nmean=1.187\nstddev=0.316"
        self.assertRasterFitsUnivar(
            raster=self.result_1, reference=values, precision=1e-3
        )

        self.assertModule(
            "r.mblend",
            high=self.high_res_2,
            low=self.low_res,
            output=self.result_2,
            far_edge=50,
        )
        self.assertRasterExists(name=self.result_2)
        values = "min=1\nmax=2\nmean=1.448\nstddev=0.417"
        self.assertRasterFitsUnivar(
            raster=self.result_2, reference=values, precision=1e-3
        )


if __name__ == "__main__":
    test()
