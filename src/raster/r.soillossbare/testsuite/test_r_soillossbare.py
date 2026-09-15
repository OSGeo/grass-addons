import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRSoillossbare(TestCase):
    elevation = "test_elevation"
    kfactor = "test_kfactor"
    rfactor = "test_rfactor"
    output = "test_soillossbare"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=10, s=0, e=10, w=0, res=1)
        cls.runModule(
            "r.mapcalc", expression=f"{cls.elevation} = row() + col()", overwrite=True
        )
        cls.runModule("r.mapcalc", expression=f"{cls.kfactor} = 0.3", overwrite=True)
        cls.runModule("r.mapcalc", expression=f"{cls.rfactor} = 100", overwrite=True)

    @classmethod
    def tearDownClass(cls):
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[cls.elevation, cls.kfactor, cls.rfactor],
        )
        cls.del_temp_region()

    def tearDown(self):
        self.runModule("g.remove", flags="f", type="raster", name=self.output)

    def test_region_preserved(self):
        """The module must not leave the user's computational region changed.

        The module sets the region to its own working resolution. Here a
        resolution (0.5) different from the current region (res 1) is used, so
        a module that does not restore the region would leave it at res 0.5.
        """
        self.runModule("g.region", n=10, s=0, e=10, w=0, res=1)
        before = gs.region()
        self.assertModule(
            "r.soillossbare",
            elevation=self.elevation,
            kfactor=self.kfactor,
            rfactor=self.rfactor,
            resolution=0.5,
            soillossbare=self.output,
            flowaccmethod="r.watershed",
            flags="r",
            overwrite=True,
        )
        after = gs.region()
        self.assertEqual(
            before,
            after,
            msg="r.soillossbare must restore the user's computational region.",
        )


if __name__ == "__main__":
    test()
