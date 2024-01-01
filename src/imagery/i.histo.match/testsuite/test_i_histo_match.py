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
        """Set region and initialize temp name"""
        cls.tmp_name = gs.tempname(12)
        gs.use_temp_region()
        gs.run_command(
            "g.region", raster=["lsat5_1987_10@landsat", "lsat7_2000_10@landsat"]
        )
        # Both input scenes have identical extent, so the mosaic equals the first input
        cls.univar_ref = """n=250325
null_cells=0
cells=250325
min=50
max=255
range=205
mean=75.7602476780186
mean_of_abs=75.7602476780186
stddev=14.402540504151
variance=207.515108919252
coeff_var=19.0106829710508
sum=18964867"""
        cls.univar_ref_2000 = """n=250325
null_cells=0
cells=250325
min=51
max=255
range=204
mean=75.5963048037551
mean_of_abs=75.5963048037551
stddev=14.6466292864087
variance=214.547156524566
coeff_var=19.3747952686718
sum=18923669"""
        cls.info_ref = """north=228513
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

    @classmethod
    def tearDownClass(cls):
        """Not needed for the module"""
        gs.del_temp_region()

    def tearDown(self):
        """Remove the output created from the module"""
        gs.run_command(
            "g.remove",
            flags="f",
            quiet=True,
            type="raster",
            pattern=f"*{self.tmp_name}*",
        )

    def test_output_created(self):
        """Check that the output is created with reference univar statistics"""
        # Run the module
        histo_match = SimpleModule(
            # Create the output with histogram matching
            "i.histo.match",
            input=["lsat5_1987_10@landsat", "lsat7_2000_10@landsat"],
            suffix=self.tmp_name,
            output=self.tmp_name,
        )
        self.assertModule(histo_match)
        # Check that output exists
        self.assertRasterExists(f"lsat5_1987_10.{self.tmp_name}")
        self.assertRasterExists(f"lsat7_2000_10.{self.tmp_name}")
        self.assertRasterExists(self.tmp_name)
        # Check unvar statistics against reference
        gs.run_command("g.region", raster=self.tmp_name, align=self.tmp_name)
        self.assertRasterFitsUnivar(
            raster=self.tmp_name, reference=self.univar_ref, precision=0.01
        )
        self.assertRasterFitsUnivar(
            raster=f"lsat5_1987_10.{self.tmp_name}",
            reference=self.univar_ref,
            precision=0.01,
        )
        self.assertRasterFitsUnivar(
            raster=f"lsat7_2000_10.{self.tmp_name}",
            reference=self.univar_ref_2000,
            precision=0.01,
        )
        # Check raster info
        self.assertRasterFitsInfo(
            raster=self.tmp_name, reference=self.info_ref, precision=0.01
        )


if __name__ == "__main__":
    test()
