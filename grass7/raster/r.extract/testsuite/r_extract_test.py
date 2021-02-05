from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.script.core import parse_command


class TestRExtract(TestCase):
    """Test case for r.extract module"""

    inp = "zipcodes"
    output = "selected_zipcodes"
    mapcalc_output = "reference_output"

    @classmethod
    def setUpClass(cls):
        """Ensures expected computational region and setup"""
        cls.use_temp_region()
        cls.runModule("g.region", raster=cls.inp)

    @classmethod
    def tearDownClass(cls):
        """Remove the temporary region"""
        cls.del_temp_region()

    def tearDown(self):
        """Remove the outputs created by r.extract.

        This is executed after each test run.
        """
        self.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[self.output, self.mapcalc_output],
        )

    def test_extract_cats(self):
        # run mapcalc for reference
        expr = "{o} = if ({i} <= 27513 || {i} == 27529 || ({i} >= 27601 && {i} <= 27605) || {i} >= 27608, {i}, null())"
        self.runModule(
            "r.mapcalc", expression=expr.format(o=self.mapcalc_output, i=self.inp)
        )
        # run the module
        self.assertModule(
            "r.extract",
            input=self.inp,
            output=self.output,
            cats="-27513,27529,27601-27605,27608-",
        )
        # check to see if output file exists
        self.assertRasterExists(self.output, msg="Output raster does not exist")
        # compare univars, because comparing rasters doesn't take nulls into account correctly
        out_univar = parse_command("r.univar", map=self.output, flags="g")
        mapcalc_univar = parse_command("r.univar", map=self.mapcalc_output, flags="g")
        self.assertDictEqual(out_univar, mapcalc_univar)

    def test_extract_clip(self):
        self.assertModule(
            "r.extract", input=self.inp, output=self.output, cats="27605", flags="c"
        )
        bbox = "rows=210\ncols=186"
        self.assertRasterFitsInfo(raster=self.output, reference=bbox)


if __name__ == "__main__":
    test()
