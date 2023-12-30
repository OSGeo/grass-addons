#!/usr/bin/env python3

"""
MODULE:    Test of  i.histo.match

AUTHOR(S): Stefan Blumentrath <stefan.blumentrath at gmx.de>

PURPOSE:   Test of  i.histo.match examples

COPYRIGHT: (C) 2023 by Stefan Blumentrath and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test
from grass.gunittest.gmodules import SimpleModule


class TestHistogramMatching(TestCase):
    """The test case for the i.histo.match module using examples from the manual"""

    @classmethod
    def setUpClass(cls):
        """Not needed for the module"""
        cls.tmp_name = gs.tempname(12)

    def tearDown(self):
        """Remove the output created from the module"""
        gs.run_command(
            "g.remove",
            flags="f",
            quiet=True,
            type="raster",
            pattern=f"*{self.tmp_name}*",
        )
        gs.utils.try_remove("")

    def test_output_created(self):
        """Check that the output is created"""
        # run the module
        histo_match = SimpleModule(
            # create the output with histogram matching
            "i.histo.match",
            input=["lsat7_2002_10", "lsat7_2002_30"],
            suffix=self.tmp_name,
            output=self.tmp_name,
        )
        self.assertModule(histo_match)
        self.assertRasterExists(f"lsat7_2002_10.{self.tmp_name}")
        self.assertRasterExists(f"lsat7_2002_30.{self.tmp_name}")
        self.assertRasterExists(self.tmp_name)
        univar_ref = """n=810
null_cells=1009790
cells=1010600
min=26
max=255
range=229
mean=77.3333333333333
mean_of_abs=77.3333333333333
stddev=31.8480574828685
variance=1014.2987654321
coeff_var=41.1828329519852
sum=62640"""
        info_ref = """north=228513
south=214975.5
east=645012
west=629992.5
nsres=28.5
ewres=28.5
rows=475
cols=527
cells=250325
datatype=CELL
ncats=0"""
        self.assertRasterFitsUnivar(
            raster=self.tmp_name, reference=univar_ref, precision=0.01
        )
        self.assertRasterFitsInfo(
            raster=self.tmp_name, reference=info_ref, precision=0.01
        )


if __name__ == "__main__":
    test()
