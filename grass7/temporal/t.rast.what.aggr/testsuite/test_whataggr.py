"""Test t.rast.whatcsv

(C) 2014 by the GRASS Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.

@author Soeren Gebbert
"""

from grass.gunittest.case import TestCase
from grass.gunittest.gmodules import SimpleModule

class TestRasterWhatAggr(TestCase):

    @classmethod
    def setUpClass(cls):
        """Initiate the temporal GIS and set the region
        """
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=80, w=0, e=120, b=0, t=50, res=10,
                      res3=10)

        cls.runModule("r.mapcalc", expression="a_1 = 100", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_2 = 200", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_3 = 300", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_4 = 400", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_5 = 500", overwrite=True)
        cls.runModule("r.mapcalc", expression="a_6 = 600", overwrite=True)

        cls.runModule("v.random", output="points", npoints=3, seed=1,
                      overwrite=True)
        cls.runModule("v.db.addtable", map="points")
        cls.runModule("v.db.addcolumn", map="points", columns="data date")
        cls.runModule("v.db.update", map="points", column="data",
                      value="2001-05-10", where="cat=1")
        cls.runModule("v.db.update", map="points", column="data",
                      value="2001-04-08", where="cat=2")
        cls.runModule("v.db.update", map="points", column="data",
                      value="2001-06-01", where="cat=3")
        cls.runModule("t.create", type="strds", temporaltype="absolute",
                      output="A",  title="A test", description="A test",
                      overwrite=True)
        cls.runModule("t.register", flags="i", type="raster", input="A",
                      maps="a_1,a_2,a_3,a_4,a_5,a_6", start="2001-01-01",
                      increment="1 months", overwrite=True)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region
        """
        cls.runModule("t.remove", flags="rf", type="strds", inputs="A")
        cls.del_temp_region()

    def test_simple(self):
        """Simpler test"""
        t_rast_what = SimpleModule("t.rast.what.aggr", strds="A",
                                   input="points", date="2001-04-01",
                                   granularity="2 months", overwrite=True,
                                   verbose=True)
        self.assertModule(t_rast_what)
        text="""1|2001-04-01|200.0
2|2001-04-01|200.0
3|2001-04-01|200.0

"""
        self.assertLooksLike(text, t_rast_what.outputs.stdout)

    def test_aflag(self):
        """Testing a flag"""
        t_rast_what = SimpleModule("t.rast.what.aggr", strds="A", flags='a',
                                   input="points", date="2001-04-01",
                                   granularity="2 months", overwrite=True,
                                   verbose=True)
        self.assertModule(t_rast_what)
        text="""1|2001-04-01|400.0
2|2001-04-01|400.0
3|2001-04-01|400.0

"""
        self.assertLooksLike(text, t_rast_what.outputs.stdout)

    def test_cflag(self):
        """Testing c flag"""
        self.assertModule(SimpleModule("t.rast.what.aggr", flags="c",
                                       strds="A", input="points",
                                       date="2001-04-01", verbose=True,
                                       granularity="2 months", overwrite=True))
        dbcols = SimpleModule("db.columns", table="points")
        self.assertModule(dbcols)
        text="""cat
data
A_average
"""
        self.assertLooksLike(text, dbcols.outputs.stdout)
        
        dbvals = SimpleModule("v.db.select", map="points")
        self.assertModule(dbvals)
        text="""cat|data|A_average
1|2001-05-10|200
2|2001-04-08|200
3|2001-06-01|200

"""
        self.assertLooksLike(text, dbvals.outputs.stdout)

    def test_methods(self):
        """Testing more methods in a single query"""
        t_rast_what = SimpleModule("t.rast.what.aggr", strds="A",
                                   input="points", date="2001-05-01",
                                   granularity="3 months", overwrite=True,
                                   method=["minimum","maximum"], verbose=True)
        self.assertModule(t_rast_what)
        text="""1|2001-05-01|200.0|300.0
2|2001-05-01|200.0|300.0
3|2001-05-01|200.0|300.0

"""
        self.assertLooksLike(text, t_rast_what.outputs.stdout)

    def test_date_column(self):
        """Testing date_column option"""
        t_rast_what = SimpleModule("t.rast.what.aggr", strds="A",
                                   input="points", date_column="data",
                                   granularity="3 months", overwrite=True,
                                   verbose=True)
        self.assertModule(t_rast_what)
        text="""2|2001-04-08|250.0
1|2001-05-10|350.0
3|2001-06-01|400.0

"""
        self.assertLooksLike(text, t_rast_what.outputs.stdout)

    def test_date_format(self):
        """Testing more methods in a single query"""
        t_rast_what = SimpleModule("t.rast.what.aggr", strds="A",
                                   input="points", date="2001/05/01",
                                   granularity="3 months", overwrite=True,
                                   method=["minimum","maximum"], verbose=True,
                                   date_format="%Y/%m/%d")
        self.assertModule(t_rast_what)
        text="""1|2001/05/01|200.0|300.0
2|2001/05/01|200.0|300.0
3|2001/05/01|200.0|300.0

"""
        self.assertLooksLike(text, t_rast_what.outputs.stdout)


class TestRasterWhatFails(TestCase):

    def test_error_handling(self):
        # No vector map, no strds, no coordinates
        self.assertModuleFail("t.rast.what.aggr", output="out.txt")
        # No vector map, no coordinates
        self.assertModuleFail("t.rast.what.aggr", strds="A", output="out.txt")
        # c flag and columns are mutually exclusive
        self.assertModuleFail("t.rast.what.aggr", flags="c",
                              strds="A", input="points", columns="average",
                              date="2001-04-01", verbose=True,
                              granularity="2 months", overwrite=True)
        # u flag and columns are mutually exclusive
        self.assertModuleFail("t.rast.what.aggr", flags="u", strds="A",
                              input="points", columns="average", verbose=True,
                              date="2001-04-01", granularity="2 months",
                              overwrite=True)

if __name__ == '__main__':
    from grass.gunittest.main import test
    test()
