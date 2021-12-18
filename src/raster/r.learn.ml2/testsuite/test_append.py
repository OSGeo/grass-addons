#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.ml

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.ml for appending RasterRows to an internal
           RasterStack object

COPYRIGHT: (C) 2020 by Steven Pawley and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""
import unittest

import grass.script as gs
from grass.script.utils import set_path

set_path("r.learn.ml2", "rlearnlib")
from rlearnlib.raster import RasterStack


class TestAppend(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """setUpClass is called once for the entire TestCase module"""
        cls.predictors = [
            "lsat7_2002_10@PERMANENT",
            "lsat7_2002_20@PERMANENT",
            "lsat7_2002_30@PERMANENT",
            "lsat7_2002_40@PERMANENT",
            "lsat7_2002_50@PERMANENT",
            "lsat7_2002_70@PERMANENT",
        ]

        # create duplicate of a landsat 2002 band from PERMANENT in a different mapset
        cls.other = "lsat7_2002_10@landsat"

        gs.run_command("g.mapset", mapset="landsat")
        gs.run_command("g.region", raster="lsat7_2002_10@PERMANENT")
        gs.mapcalc("lsat7_2002_10 = lsat7_2002_10@PERMANENT")
        gs.run_command("g.mapset", mapset="PERMANENT")

    @classmethod
    def tearDownClass(cls) -> None:
        """remove temporary maps after all tests"""
        gs.run_command("g.mapset", mapset="landsat")
        gs.run_command("g.remove", type="raster", name=cls.other, flags="f")
        gs.run_command("g.mapset", mapset="PERMANENT")

    def test_append(self):
        """Append another grass raster to a RasterStack"""
        stack = RasterStack(self.predictors[0:5])
        stack.append(self.predictors[5])
        self.assertListEqual(stack.names, self.predictors)

    def test_append_with_copy(self):
        """Append another grass raster to a RasterStack not modifying
        in_place"""
        stack = RasterStack(self.predictors[0:5])
        other = stack.append(self.predictors[5], in_place=False)
        self.assertListEqual(other.names, self.predictors)
        self.assertListEqual(stack.names, self.predictors[0:5])

    @unittest.expectedFailure
    def test_append_identical(self):
        """Append another grass raster containing a single layer with an
        identical name and mapset

        Expected that this will fail because the name and mapset is identical
        and a RasterStack has index keys based on fullnames
        """
        stack = RasterStack(self.predictors)
        stack.append(self.predictors[5], in_place=True)

    def test_append_diff_mapset(self):
        """Append another grass raster containing a single layer that has an
        identical name but is in a different mapset

        Expected that this will pass because the name is identical but the
        mapset is different and a RasterStack has index keys based on
        fullnames
        """
        stack = RasterStack(self.predictors)
        stack.append(self.other, in_place=True)


if __name__ == "__main__":
    unittest.main()
