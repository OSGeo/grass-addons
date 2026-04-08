import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


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
        cls.runModule(
            "r.in.gdal",
            input=f"data/{cls.lc}.tif",
            output=cls.lc,
            flags="o",
            overwrite=True,
        )
        cls.runModule(
            "r.in.gdal",
            input=f"data/{cls.hsg}.tif",
            output=cls.hsg,
            flags="o",
            overwrite=True,
        )
        cls.runModule(
            "r.in.gdal",
            input=f"data/{cls.expected}.tif",
            output=cls.expected,
            flags="o",
            overwrite=True,
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

    def test_esa_against_expected(self):
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
            overwrite=True,
        )

        # 3) difference must be zero everywhere
        stats = gs.parse_command("r.univar", flags="g", map=self.diff)

        self.assertAlmostEqual(
            float(stats["min"]), 0.0, msg="Difference minimum is not zero"
        )

        self.assertAlmostEqual(
            float(stats["max"]), 0.0, msg="Difference maximum is not zero"
        )


class TestDualHSG(TestCase):
    """Test dual HSG resolution and null-soil fallback."""

    lc_single = "lc_dual_test"
    hsg_dual = "hsg_dual_test"
    hsg_single_a = "hsg_single_a_test"
    hsg_single_d = "hsg_single_d_test"
    lc_null = "lc_null_test"
    hsg_null = "hsg_null_test"
    hsg_d_only = "hsg_d_only_test"
    hsg_invalid = "hsg_invalid_test"
    out_drained = "cn_drained"
    out_undrained = "cn_undrained"
    out_expected_a = "cn_expected_a"
    out_expected_d = "cn_expected_d"
    out_null_soil = "cn_null_soil"
    out_null_expected = "cn_null_expected"
    out_null_lc = "cn_null_lc"
    out_invalid_hsg = "cn_invalid_hsg"
    diff = "cn_dual_diff"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=3, s=0, e=3, w=0, rows=1, cols=1, res=3)

        # landcover = ESA 30 (grassland), single pixel
        cls.runModule("r.mapcalc", expression=f"{cls.lc_single} = 30")
        # dual HSG A/D = 11
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_dual} = 11")
        # single HSG A = 1 (expected result for drained)
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_single_a} = 1")
        # single HSG D = 4 (expected result for undrained)
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_single_d} = 4")
        # null landcover raster
        cls.runModule("r.mapcalc", expression=f"{cls.lc_null} = null()")
        # null soil raster
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_null} = null()")
        # HSG D only (expected result for null soil fallback)
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_d_only} = 4")
        # invalid HSG value
        cls.runModule("r.mapcalc", expression=f"{cls.hsg_invalid} = 99")

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=(
                cls.lc_single,
                cls.lc_null,
                cls.hsg_dual,
                cls.hsg_single_a,
                cls.hsg_single_d,
                cls.hsg_null,
                cls.hsg_d_only,
                cls.hsg_invalid,
            ),
        )

    def tearDown(self):
        self.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=(
                self.out_drained,
                self.out_undrained,
                self.out_expected_a,
                self.out_expected_d,
                self.out_null_soil,
                self.out_null_expected,
                self.out_null_lc,
                self.out_invalid_hsg,
                self.diff,
            ),
        )

    def test_dual_hsg_drained(self):
        """Dual HSG A/D with -d flag should match single HSG A."""
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_dual,
            landcover_source="esa",
            flags="d",
            output=self.out_drained,
        )
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_single_a,
            landcover_source="esa",
            output=self.out_expected_a,
        )
        self.runModule(
            "r.mapcalc",
            expression=f"{self.diff} = {self.out_drained} - {self.out_expected_a}",
        )
        stats = gs.parse_command("r.univar", flags="g", map=self.diff)
        self.assertAlmostEqual(
            float(stats["min"]), 0.0, msg="Drained dual HSG A/D != single HSG A"
        )
        self.assertAlmostEqual(
            float(stats["max"]), 0.0, msg="Drained dual HSG A/D != single HSG A"
        )

    def test_dual_hsg_undrained(self):
        """Dual HSG A/D without -d flag should match single HSG D."""
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_dual,
            landcover_source="esa",
            output=self.out_undrained,
        )
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_single_d,
            landcover_source="esa",
            output=self.out_expected_d,
        )
        self.runModule(
            "r.mapcalc",
            expression=f"{self.diff} = {self.out_undrained} - {self.out_expected_d}",
        )
        stats = gs.parse_command("r.univar", flags="g", map=self.diff)
        self.assertAlmostEqual(
            float(stats["min"]), 0.0, msg="Undrained dual HSG A/D != single HSG D"
        )
        self.assertAlmostEqual(
            float(stats["max"]), 0.0, msg="Undrained dual HSG A/D != single HSG D"
        )

    def test_invalid_hsg_produces_null(self):
        """Invalid HSG value should produce null output."""
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_invalid,
            landcover_source="esa",
            output=self.out_invalid_hsg,
        )
        stats = gs.parse_command("r.univar", flags="g", map=self.out_invalid_hsg)
        self.assertEqual(
            int(stats["n"]), 0, msg="Invalid HSG should produce all null cells"
        )

    def test_null_landcover_produces_null(self):
        """Null landcover should produce null output."""
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_null,
            soil=self.hsg_single_d,
            landcover_source="esa",
            output=self.out_null_lc,
        )
        stats = gs.parse_command("r.univar", flags="g", map=self.out_null_lc)
        self.assertEqual(
            int(stats["n"]), 0, msg="Null landcover should produce all null cells"
        )

    def test_null_soil_fallback(self):
        """Null soil with valid landcover should fall back to HSG D."""
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_null,
            landcover_source="esa",
            output=self.out_null_soil,
        )
        self.assertModule(
            "r.curvenumber",
            landcover=self.lc_single,
            soil=self.hsg_d_only,
            landcover_source="esa",
            output=self.out_null_expected,
        )
        self.runModule(
            "r.mapcalc",
            expression=f"{self.diff} = {self.out_null_soil} - {self.out_null_expected}",
        )
        stats = gs.parse_command("r.univar", flags="g", map=self.diff)
        self.assertAlmostEqual(
            float(stats["min"]), 0.0, msg="Null soil fallback != HSG D"
        )
        self.assertAlmostEqual(
            float(stats["max"]), 0.0, msg="Null soil fallback != HSG D"
        )


if __name__ == "__main__":
    test()
