#!/usr/bin/env python3

"""
MODULE:    Test of r.viewshed.exposure
AUTHOR(S): Stefan Blumentrath <stefan dot blumentrath at nina dot no>
           Zofie Cimburova
PURPOSE:   Test of r.viewshed.exposure
COPYRIGHT: (C) 2020 by Stefan Blumentrath, Zofie Cimburova and the GRASS GIS
Development Team
This program is free software under the GNU General Public
License (>=v2). Read the file COPYING that comes with GRASS
for details.
"""

from grass.gunittest.gmodules import SimpleModule
import grass.script as gs

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestFunctions(TestCase):
    """The main (and only) test case for the r.viewshed.exposure module"""

    tempname = gs.tempname(12)

    # Raster maps used as inputs
    source_roads = "roadsmajor@PERMANENT"
    source_lakes = "lakes@PERMANENT"
    source_points = "geodetic_swwake_pts@PERMANENT"
    dsm = "elevation@PERMANENT"

    functions = [
        "Binary",
        "Fuzzy_viewshed",
        "Distance_decay",
        "Solid_angle",
        "Visual_magnitude",
    ]

    r_viewshed = SimpleModule(
        "r.viewshed.exposure",
        flags="cr",
        input=dsm,
        source=source_roads,
        observer_elevation=1.5,
        range=100,
        b1_distance=10,
        sample_density=5,
        seed=50,
        memory=5000,
        cores=10,
        quiet=True,
        overwrite=True,
    )

    test_results_stats = {
        "test_roads_B": {
            "n": 120880,
            "null_cells": 1904120,
            "cells": 2025000,
            "min": 0,
            "max": 15,
            "range": 15,
            "mean": 1.62403,
            "mean_of_abs": 1.62403,
            "stddev": 1.93013,
            "variance": 3.72542,
            "coeff_var": 118.848259976884,
            "sum": 196313,
        },
        "test_roads_F": {
            "n": 120880,
            "null_cells": 1904120,
            "cells": 2025000,
            "min": 0,
            "max": 11.3565,
            "range": 11.3565,
            "mean": 1.20334,
            "mean_of_abs": 1.20334,
            "stddev": 1.47689,
            "variance": 2.18121,
            "coeff_var": 122.732631198116,
            "sum": 145459.99071890,
        },
        "test_roads_D": {
            "n": 120880,
            "null_cells": 1904120,
            "cells": 2025000,
            "min": 0,
            "max": 3.86,
            "range": 3.86,
            "mean": 0.118786,
            "mean_of_abs": 0.118786,
            "stddev": 0.275875,
            "variance": 0.076107,
            "coeff_var": 232.246,
            "sum": 14358.8130874699,
        },
        "test_roads_S": {
            "n": 120749,
            "null_cells": 1904251,
            "cells": 2025000,
            "min": 0,
            "max": 3.00867,
            "range": 3.00867,
            "mean": 0.0232121,
            "mean_of_abs": 0.0232121,
            "stddev": 0.202763,
            "variance": 0.0411129,
            "coeff_var": 873.523497082485,
            "sum": 2802.8384487502,
        },
        "test_roads_V": {
            "n": 120749,
            "null_cells": 1904251,
            "cells": 2025000,
            "min": 0,
            "max": 45.2416,
            "range": 45.2416,
            "mean": 0.34082,
            "mean_of_abs": 0.34082,
            "stddev": 3.80045,
            "variance": 14.4434,
            "coeff_var": 1115.09106861343,
            "sum": 41153.6541857501,
        },
        "test_lakes": {
            "n": 75396,
            "null_cells": 1949604,
            "cells": 2025000,
            "min": 0,
            "max": 4.61498,
            "range": 4.61498,
            "mean": 0.422226,
            "mean_of_abs": 0.422226,
            "stddev": 0.555438,
            "variance": 0.308511,
            "coeff_var": 131.549853569661,
            "sum": 31834.1479829689,
        },
        "test_points": {
            "n": 97340,
            "null_cells": 1927660,
            "cells": 2025000,
            "min": 0,
            "max": 11.8462,
            "range": 11.8462,
            "mean": 0.0432476,
            "mean_of_abs": 0.0432476,
            "stddev": 0.144737,
            "variance": 0.0209488,
            "coeff_var": 334.670567638394,
            "sum": 4209.72256931104,
        },
    }

    @classmethod
    def setUpClass(cls):
        """Save the current region
        We cannot use temp_region as it is used by the module.
        """

        # Save current region to temporary file
        cls.runModule("g.region", flags="u", save="{}_region".format(cls.tempname))

    @classmethod
    def tearDownClass(cls):
        """Reset original region and remove the temporary region"""
        cls.runModule("g.region", region="{}_region".format(cls.tempname))
        cls.runModule(
            "g.remove", flags="f", type="region", name="{}_region".format(cls.tempname)
        )

    def tearDown(self):
        """Remove the output created from the module
        This is executed after each test function run. If we had
        something to set up before each test function run, we would use setUp()
        function.
        Since we remove the raster map after running each test function,
        we can reuse the same name for all the test functions.
        """
        self.runModule("g.remove", flags="f", type="raster", pattern="test_2*")

    def test_roads(self):
        """Test exposure to roads using all viewshed parametrisation functions"""

        # Use the input DSM to set computational region
        gs.run_command("g.region", raster=self.dsm, align=self.dsm)

        for function in self.functions:

            # Output dataset
            output = "test_roads_{}".format(function[0])
            self.r_viewshed.outputs.output = output

            # Input datasets
            self.r_viewshed.inputs.input = self.dsm
            self.r_viewshed.inputs.source = self.source_roads
            self.r_viewshed.inputs.function = function
            self.r_viewshed.inputs.sampling_points = None

            # # Print the command
            # print(self.r_viewshed.get_bash())

            # Check that the module runs
            self.assertModule(self.r_viewshed)

            # Check to see if output is in mapset
            self.assertRasterExists(output, msg="Output was not created")

            # Here we need to check if univariate raster statistics match the expected result
            self.assertRasterFitsUnivar(
                raster=output,
                reference=self.test_results_stats[output],
                precision=1e-4,
            )

    def test_lakes(self):
        """Test exposure to lakes."""

        # Use the input DSM to set computational region
        gs.run_command("g.region", raster=self.dsm, align=self.dsm)

        function = "Distance_decay"

        # Output dataset
        output = "test_lakes"
        self.r_viewshed.outputs.output = output

        # Input dataset
        self.r_viewshed.inputs.input = self.dsm
        self.r_viewshed.inputs.source = self.source_lakes
        self.r_viewshed.inputs.function = function

        # # Print the command
        # print(self.r_viewshed.get_bash())

        # Check that the module runs
        self.assertModule(self.r_viewshed)

        # Check to see if output is in mapset
        self.assertRasterExists(output, msg="Output was not created")

        # Here we need to check if univariate raster statistics match the expected result
        self.assertRasterFitsUnivar(
            raster=output,
            reference=self.test_results_stats[output],
            precision=1e-5,
        )

    def test_points(self):
        """Test exposure from points"""

        # Use of of the input dsm to set computational region
        gs.run_command("g.region", raster=self.dsm, align=self.dsm)

        function = "Distance_decay"

        # Output datasets
        output = "test_points"
        self.r_viewshed.outputs.output = output

        # Input datasets
        self.r_viewshed.inputs.input = self.dsm
        self.r_viewshed.inputs.source = None
        self.r_viewshed.inputs.sampling_points = self.source_points
        self.r_viewshed.inputs.function = function

        # # Print command
        # print(self.r_viewshed.get_bash())

        # Check that the module runs
        self.assertModule(self.r_viewshed)

        # Check to see if output is in mapset
        self.assertRasterExists(output, msg="Output was not created")

        # Here we need to check if univariate raster statistics match the expected result
        self.assertRasterFitsUnivar(
            raster=output,
            reference=self.test_results_stats[output],
            precision=1e-4,
        )


if __name__ == "__main__":
    test()
