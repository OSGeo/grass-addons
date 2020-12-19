"""Test t.rast.whatcsv

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule

class TestRasterWhatCSV(TestCase):

    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region
        """
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=80, w=0, e=120, b=0, t=50, res=10, res3=10)

        cls.runModule("r.mapcalc", expression="a_1 = 100", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = 200", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = 300", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = 400", overwrite=True)

        csv_file = open("test.csv", "w")
        csv_file.write("1|115.0043586274|36.3593955783|2001-01-01 00:00:00\n")
        csv_file.write("2|79.6816763826|45.2391522853|2001-04-01 00:00:00\n")
        csv_file.write("3|97.4892579600|79.2347263950|2001-07-01 00:00:00\n")
        csv_file.write("4|115.0043586274|36.3593955783|2001-11-01 00:00:00\n")
        csv_file.close()

        cls.runModule("t.create", type="strds", temporaltype="absolute",
                                 output="A", title="A test", description="A test",
                                 overwrite=True)
        cls.runModule("t.register", flags="i", type="raster", input="A",
                                     maps="a_1,a_2,a_3,a_4", start="2001-01-01",
                                     increment="3 months", overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region
        """
        cls.runModule("t.remove", flags="rf", type="strds",
                                   inputs="A")
        cls.del_temp_region()

    def test_1t(self):

        t_rast_whatcsv = SimpleModule("t.rast.whatcsv", strds="A",
                                      csv="test.csv", overwrite=True,
                                      skip=0, verbose=True)
        self.assertModule(t_rast_whatcsv)

        text = """1|115.0043586274|36.3593955783||100
2|79.6816763826|45.2391522853||200
3|97.4892579600|79.2347263950||300
4|115.0043586274|36.3593955783||400
"""
        self.assertLooksLike(text, t_rast_whatcsv.outputs.stdout)

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
