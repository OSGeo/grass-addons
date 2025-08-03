from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestREarthworks(TestCase):
    input = "test_input"
    cut = "test_cut"
    fill = "test_fill"
    cutfill = "test_cutfill"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=10, s=0, e=10, w=0, res=1)
        cls.runModule("r.mapcalc", expression=f"{cls.input} = 0")

    @classmethod
    def tearDownClass(cls):
        cls.runModule("g.remove", flags="f", type="raster", name=cls.input)
        cls.del_temp_region()

    def tearDown(cls):
        """Remove output maps"""
        cls.runModule(
            "g.remove", flags="f", type="raster", name=[cls.fill, cls.cut, cls.cutfill]
        )

    def test_fill_operation(self):
        """Test fill operation"""
        self.assertModule(
            "r.earthworks",
            elevation=self.input,
            earthworks=self.fill,
            coordinates=[5, 5],
            operation="fill",
            z=1,
            flat=2,
            rate=0.5,
        )
        self.assertRasterMinMax(
            map=self.fill, refmin=0, refmax=1, msg="Elevation must be between 0 and 1."
        )
        self.assertRasterExists(name=self.fill, msg="Output was not created.")

    def test_cut_operation(self):
        """Test cut operation"""
        self.assertModule(
            "r.earthworks",
            elevation=self.input,
            earthworks=self.cut,
            coordinates=[5, 5],
            operation="cut",
            z=-1,
            flat=2,
            rate=0.5,
        )
        self.assertRasterMinMax(
            map=self.cut, refmin=-1, refmax=0, msg="Elevation must be between -1 and 0."
        )
        self.assertRasterExists(name=self.cut, msg="Output was not created")

    def test_cutfill_operation(self):
        """Test cut & fill operation"""
        self.assertModule(
            "r.earthworks",
            elevation=self.input,
            earthworks=self.cutfill,
            coordinates=[3, 3, 7, 7],
            operation="cutfill",
            z=[-1, 1],
            flat=1,
            rate=0.5,
        )
        self.assertRasterMinMax(
            map=self.cutfill,
            refmin=-1,
            refmax=1,
            msg="Elevation must be between -1 and 1.",
        )
        self.assertRasterExists(name=self.cutfill, msg="Output was not created.")


if __name__ == "__main__":
    test()
