#!/usr/bin/env python3

############################################################################
#
# NAME:      test_r_colors_out_sld
#
# PURPOSE:   Tests for r.colors.out_sld
#
# COPYRIGHT: (C) 2026 by bhuvan-somisetty and the GRASS Development Team
#
#            This program is free software under the GNU General Public
#            License (>=v2). Read the file COPYING that comes with GRASS
#            for details.
#
#############################################################################

import os
import tempfile

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestRColorsOutSld(TestCase):
    test_raster_cell = "test_sld_cell"
    test_raster_dcell = "test_sld_dcell"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=10, s=0, w=0, e=10, res=1)
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.test_raster_cell} = (row() - 1) * 10 + col()",
            overwrite=True,
        )
        cls.runModule(
            "r.mapcalc",
            expression=f"{cls.test_raster_dcell} = ((row() - 1) * 10 + col()) * 1.5",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[cls.test_raster_cell, cls.test_raster_dcell],
        )

    def test_cell_without_categories(self):
        """Test CELL map without category labels does not crash with KeyError or IndexError."""
        output_path = os.path.join(tempfile.gettempdir(), "test_cell_no_cats.sld")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.assertModule(
                "r.colors.out_sld",
                map=self.test_raster_cell,
                output=output_path,
            )
            self.assertTrue(os.path.isfile(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("StyledLayerDescriptor", content)
            self.assertIn("<ColorMap>", content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_cell_with_categories(self):
        """Test CELL map with category labels uses values colormap and labels."""
        labeled_raster = "test_sld_labeled"
        output_path = os.path.join(tempfile.gettempdir(), "test_cell_with_cats.sld")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.runModule(
                "r.mapcalc",
                expression=f"{labeled_raster} = if(col() <= 5, 1, 2)",
                overwrite=True,
            )
            rules = "1=Forest\n2=Water\n"
            self.runModule(
                "r.category",
                map=labeled_raster,
                separator="=",
                rules="-",
                stdin=rules,
            )
            self.assertModule(
                "r.colors.out_sld",
                map=labeled_raster,
                output=output_path,
            )
            self.assertTrue(os.path.isfile(output_path))
            with open(output_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn('type="values"', content)
            self.assertIn('label="Forest"', content)
            self.assertIn('label="Water"', content)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.runModule("g.remove", flags="f", type="raster", name=[labeled_raster])

    def test_dcell_raster(self):
        """Test DCELL raster generates valid SLD without error."""
        output_path = os.path.join(tempfile.gettempdir(), "test_dcell.sld")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.assertModule(
                "r.colors.out_sld",
                map=self.test_raster_dcell,
                output=output_path,
            )
            self.assertTrue(os.path.isfile(output_path))
            self.assertGreater(os.path.getsize(output_path), 0)
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_overwrite_protection(self):
        """Test that existing output file fails without overwrite and succeeds with overwrite."""
        output_path = os.path.join(tempfile.gettempdir(), "test_overwrite.sld")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.assertModule(
                "r.colors.out_sld",
                map=self.test_raster_cell,
                output=output_path,
            )
            self.assertTrue(os.path.isfile(output_path))
            # Attempt without overwrite should fail
            self.assertModuleFail(
                "r.colors.out_sld",
                map=self.test_raster_cell,
                output=output_path,
            )
            # Attempt with overwrite should succeed
            self.assertModule(
                "r.colors.out_sld",
                map=self.test_raster_cell,
                output=output_path,
                overwrite=True,
            )
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_fails_on_missing_map(self):
        """Test failure when map does not exist."""
        self.assertModuleFail("r.colors.out_sld", map="non_existent_map_12345")


if __name__ == "__main__":
    test()
