"""Test v.rast.bufferstats

(C) 2021 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Stefan Blumentrath

# Tabulate area of land cover map
g.region -p raster=elevation,geology_30m align=geology_30m
v.rast.bufferstats -t input=bridges_wake raster=geology_30m \
buffers=100,250,500 column_prefix=geology

# Compute terrain statistics
g.region -p raster=elevation,geology_30m align=elevation
r.slope.aspect elevation=elevation slope=slope aspect=aspect
v.rast.bufferstats input=bridges_wake raster=elevation,slope,aspect \
buffers=100,250,500 column_prefix=altitude,slope,aspect \
methods=minimum,maximum,average,stddev percentile=5,95

"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule


class TestBufferstatsTab(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        cls.use_temp_region()
        cls.runModule("g.region", raster="geology_30m", align="geology_30m")
        cls.runModule("v.clip", flags="r", input="bridges", output="bridges_wake")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.runModule("g.remove", flags="f", type="vector", name="bridges_wake")

    def test_tabulation_no_labels(self):

        tabulation_no_labels = SimpleModule(
            "v.rast.bufferstats",
            flags="t",
            input="bridges_wake",
            raster="geology_30m",
            buffers=[150],
            column_prefix="geology",
            verbose=True,
        )
        self.assertModule(tabulation_no_labels)

    def test_tabulation_no_labels_update(self):

        tabulation_no_labels_update = SimpleModule(
            "v.rast.bufferstats",
            flags="tu",
            input="bridges_wake",
            raster="geology_30m",
            buffers=[150],
            column_prefix="geology",
            verbose=True,
        )
        self.assertModule(tabulation_no_labels_update)

    """
    def test_tabulation_no_labels_update_fail(self):

        tabulation_no_labels_update_fail = SimpleModule("v.rast.bufferstats", flags="t",
                                         input="bridges_wake",
                                         raster="geology_30m",
                                         buffers=[150],
                                         column_prefix="geology",
                                         verbose=True)
        self.assertModuleFail(tabulation_no_labels_update_fail)
    """


class TestBufferstatsTabLab(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        cls.use_temp_region()
        cls.runModule("g.region", raster="geology_30m", align="geology_30m")
        cls.runModule("v.clip", flags="r", input="bridges", output="bridges_wake_lab")

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.runModule("g.remove", flags="f", type="vector", name="bridges_wake_lab")

    def test_tabulation_labels(self):

        tabulation_labels = SimpleModule(
            "v.rast.bufferstats",
            flags="tl",
            input="bridges_wake_lab",
            raster="geology_30m",
            buffers=[150],
            column_prefix="geology",
            verbose=True,
        )
        self.assertModule(tabulation_labels)

    def test_tabulation_labels_update(self):

        tabulation_labels_update = SimpleModule(
            "v.rast.bufferstats",
            flags="ltu",
            input="bridges_wake_lab",
            raster="geology_30m",
            buffers=[150],
            column_prefix="geology",
            verbose=True,
        )
        self.assertModule(tabulation_labels_update)

    """
    def test_tabulation_labels_update_fail(self):

        tabulation_labels_update_fail = SimpleModule("v.rast.bufferstats", flags="tl",
                                         input="bridges_wake",
                                         raster="geology_30m",
                                         buffers=[150],
                                         column_prefix="geology",
                                         verbose=True)
        self.assertModuleFail(tabulation_labels_update_fail)
    """


class TestBufferstatsNum(TestCase):
    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region"""
        cls.use_temp_region()
        cls.runModule("g.region", raster="geology_30m", align="geology_30m")
        cls.runModule("v.clip", flags="r", input="bridges", output="bridges_wake_num")
        cls.runModule(
            "r.slope.aspect", elevation="elevation", slope="slope", aspect="aspect"
        )

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.runModule("g.remove", flags="f", type="vector", name="bridges_wake_num")
        cls.runModule("g.remove", flags="f", type="raster", name="slope,aspect")

    def test_multiple_numeric(self):

        multiple_numeric_mod = SimpleModule(
            "v.rast.bufferstats",
            input="bridges_wake_num",
            raster="elevation,slope,aspect",
            buffers=[100, 250, 500],
            column_prefix="altitude,slope,aspect",
            methods=["minimum", "maximum", "average", "stddev"],
            percentile=[5, 95],
            verbose=True,
        )
        self.assertModule(multiple_numeric_mod)

    def test_multiple_numeric_update(self):

        multiple_numeric_update_mod = SimpleModule(
            "v.rast.bufferstats",
            flags="u",
            input="bridges_wake_num",
            raster="elevation,slope,aspect",
            buffers=[100, 250, 500],
            column_prefix="altitude,slope,aspect",
            methods=["minimum", "maximum", "average", "stddev"],
            percentile=[5, 95],
            verbose=True,
        )
        self.assertModule(multiple_numeric_update_mod)

    """
    def test_tabulation_labels_update_fail(self):

        tabulation_labels_update_fail = SimpleModule("v.rast.bufferstats", flags="tl",
                                         input="bridges_wake",
                                         raster="geology_30m",
                                         buffers=[150],
                                         column_prefix="geology",
                                         verbose=True)
        self.assertModuleFail(tabulation_labels_update_fail)
    """


if __name__ == "__main__":
    from grass.gunittest.main import test

    test()
