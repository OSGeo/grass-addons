#!/usr/bin/env python3

"""
MODULE:    Test of r.learn.ml

AUTHOR(S): Steven Pawley <dr.stevenpawley gmail com>

PURPOSE:   Test of r.learn.ml for dropping RasterRow objects from an internal
           RasterStack object

COPYRIGHT: (C) 2020 by Steven Pawley and the GRASS Development Team

This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

import unittest

from grass.script.utils import set_path

set_path("r.learn.ml2", "rlearnlib")
from rlearnlib.raster import RasterStack


class MyTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        """Setup that is run once for the entire test module"""
        cls.predictors = [
            "lsat7_2002_10@PERMANENT",
            "lsat7_2002_20@PERMANENT",
            "lsat7_2002_30@PERMANENT",
            "lsat7_2002_40@PERMANENT",
            "lsat7_2002_50@PERMANENT",
            "lsat7_2002_70@PERMANENT"
        ]

    def setUp(self) -> None:
        """Setup that is run before every test"""
        self.stack = RasterStack(self.predictors)

    def test_drop_single_label(self):
        """Test dropping a single RasterRow object from a RasterStack using
        a label"""
        self.stack.drop("lsat7_2002_70@PERMANENT", in_place=True)
        self.assertListEqual(self.stack.names, self.predictors[0:5])

    def test_drop_shortname(self):
        """Test dropping a single RasterRow object from a RasterStack using
        a label based on only the shortname of a raster, i.e. it's name
        but not it's mapset. This should pass because a RasterStack uses the
        same procedure as GRASS to find the mapset for a raster name where
        the mapset is not specified explicitly"""

        self.stack.drop("lsat7_2002_70", in_place=True)
        self.assertListEqual(self.stack.names, self.predictors[0:5])


if __name__ == '__main__':
    unittest.main()
