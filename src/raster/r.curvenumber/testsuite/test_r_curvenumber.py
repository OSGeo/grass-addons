import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestRCn(TestCase):
    """Test r.curvenumber against a known expected output raster."""

    lc = "lc_esa_test"
    hsg = "hsg_test"
    expected = "cn_esa_expected"
    computed = "cn_esa_computed"
    diff = "cn_diff"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("r.in.gdal", input=f"data/{cls.lc}.tif", output=cls.lc, flags="o")
        cls.runModule(
            "r.in.gdal", input=f"data/{cls.hsg}.tif", output=cls.hsg, flags="o"
        )
        cls.runModule(
            "r.in.gdal",
            input=f"data/{cls.expected}.tif",
            output=cls.expected,
            flags="o",
        )
        cls.runModule("g.region", raster=cls.lc)

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove", flags="f", type="raster", name=(cls.lc, cls.hsg, cls.expected)
        )

    def tearDown(self):
        self.runModule(
            "g.remove", flags="f", type="raster", name=(self.computed, self.diff)
        )

    def test_nlcd_against_expected(self):
        """Run r.curvenumber with source=esa and verify pixel-perfect match."""
        # 1) compute CN with r.curvenumber module
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc,
            soil=self.hsg,
            landcover_source="esa",
            output=self.computed,
            overwrite=True,
        )

        # 2) subtract expected from computed
        self.runModule(
            "r.mapcalc",
            expression=f"{self.diff} = {self.computed} - {self.expected}",
        )

        # 3) difference must be zero everywhere
        stats = gs.parse_command("r.univar", flags="g", map=self.diff)

        self.assertAlmostEqual(
            float(stats["min"]), 0.0, msg="Difference minimum is not zero"
        )

        self.assertAlmostEqual(
            float(stats["max"]), 0.0, msg="Difference maximum is not zero"
        )


if __name__ == "__main__":
    test()
