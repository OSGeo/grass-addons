#!/usr/bin/env python3

############################################################################
#
# NAME:      test_r_boxplot
#
# AUTHOR:    Rajveer Bishnoi
#
# PURPOSE:   Tests for r.boxplot
#
# SPDX-FileCopyrightText: 2025 Rajveer Bishnoi
# SPDX-FileCopyrightText: Other GRASS authors
# SPDX-License-Identifier: GPL-2.0-or-later
#############################################################################

import os
import tempfile

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRBoxplot(TestCase):
    value_raster = "test_boxplot_values"
    zones_raster = "test_boxplot_zones"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=10, s=0, w=0, e=10, res=1)
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.value_raster} = (row() - 1) * 10 + col()",
            overwrite=True,
        )
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.zones_raster} = if(col() <= 5, 1, 2)",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[cls.value_raster, cls.zones_raster],
        )

    def test_output_file_created(self):
        """Module produces an output file when output= is given"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
        try:
            self.assertModule(
                "r.boxplot",
                map=self.value_raster,
                output=output_path,
                overwrite=True,
            )
            self.assertTrue(
                os.path.isfile(output_path),
                msg=f"Expected output file not found: {output_path}",
            )
            self.assertGreater(
                os.path.getsize(output_path),
                0,
                msg="Output file is empty",
            )
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_zonal_output_file_created(self):
        """Module produces an output file when zones= is given"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
        try:
            self.assertModule(
                "r.boxplot",
                map=self.value_raster,
                zones=self.zones_raster,
                output=output_path,
                overwrite=True,
            )
            self.assertTrue(
                os.path.isfile(output_path),
                msg=f"Expected output file not found: {output_path}",
            )
            self.assertGreater(
                os.path.getsize(output_path),
                0,
                msg="Output file is empty",
            )
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_fails_without_required_input(self):
        """Module exits with error when required map= parameter is missing"""
        output_path = os.path.join(tempfile.gettempdir(), "r_boxplot_no_input.png")
        try:
            self.assertModuleFail("r.boxplot", output=output_path)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_fails_with_float_zones(self):
        """Module exits with error when zones raster is not integer type"""
        float_raster = "test_boxplot_float_zones"
        output_path = os.path.join(tempfile.gettempdir(), "r_boxplot_float_zones.png")
        try:
            self.runModule(
                "r.mapcalc",
                expression=f"{float_raster} = 1.5",
                overwrite=True,
            )
            self.assertModuleFail(
                "r.boxplot",
                map=self.value_raster,
                zones=float_raster,
                output=output_path,
            )
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.runModule("g.remove", flags="f", type="raster", name=[float_raster])

    def test_horizontal_orientation(self):
        """Module runs successfully with horizontal flag"""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            output_path = f.name
        try:
            self.assertModule(
                "r.boxplot",
                map=self.value_raster,
                output=output_path,
                flags="h",
                overwrite=True,
            )
            self.assertTrue(os.path.isfile(output_path))
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)


if __name__ == "__main__":
    test()
