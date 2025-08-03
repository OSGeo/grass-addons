from grass.gunittest.case import TestCase


class TestRSimSediment(TestCase):
    """Test r.stone"""

    # Set up the necessary raster maps for testing
    dem = "dem"
    sources = "sources"
    friction = "friction"
    nrest = "nrest"
    trest = "trest"
    expectedcount = "expectedcount"
    count = "count"

    @classmethod
    def setUpClass(cls):
        """Set up region, create necessary data"""

        cls.runModule("g.region", w=-1786670, e=-1786030, n=2463964, s=2463504, res=10)
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/dem.pack",
            output=cls.dem,
        )
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/sources.pack",
            output=cls.sources,
        )
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/friction.pack",
            output=cls.friction,
        )
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/nrest.pack",
            output=cls.nrest,
        )
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/trest.pack",
            output=cls.trest,
        )
        cls.runModule(
            "r.unpack",
            flags="o",
            input="data/expectedcount.pack",
            output=cls.expectedcount,
        )

    @classmethod
    def tearDownClass(cls):
        """Clean up test environment"""
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[
                cls.dem,
                cls.sources,
                cls.friction,
                cls.nrest,
                cls.trest,
                cls.expectedcount,
                cls.count,
            ],
        )

    def test_default(self):
        """Test r.stone with default parameters"""

        self.assertModule(
            "r.stone",
            dem=self.dem,
            sources=self.sources,
            friction=self.friction,
            nrest=self.nrest,
            trest=self.trest,
            counter=self.count,
            ang_stoch_range=10,
            vrest_stoch_range=10,
            hrest_stoch_range=10,
            frict_stoch_range=10,
            stop_vel=1,
            start_vel=0.5,
            stoch_funct_ang=0,
            stoch_funct=0,
        )

        # Assert that the output raster exists
        self.assertRasterExists(self.count)
        # Assert that the output rasters are the same
        self.assertRastersEqual(self.count, reference=self.expectedcount, precision="1")


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
