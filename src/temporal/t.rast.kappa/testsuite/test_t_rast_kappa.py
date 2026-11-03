#!/usr/bin/env python3

############################################################################
#
# NAME:      test_t_rast_kappa
#
# PURPOSE:   Tests for t.rast.kappa
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

import grass.script as gs
import grass.temporal as tgis
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestTRastKappa(TestCase):
    strds_name = "test_kappa_strds"
    map_names = ["test_k_1", "test_k_2", "test_k_3", "test_k_4"]

    @classmethod
    def setUpClass(cls):
        tgis.init(raise_fatal_error=True)
        cls.use_temp_region()
        cls.runModule("g.region", s=0, n=20, w=0, e=20, res=10)

        cls.runModule("r.mapcalc", expression="test_k_1 = 1", overwrite=True)
        cls.runModule("r.mapcalc", expression="test_k_2 = 1", overwrite=True)
        cls.runModule("r.mapcalc", expression="test_k_3 = 2", overwrite=True)
        cls.runModule("r.mapcalc", expression="test_k_4 = 2", overwrite=True)

        cls.runModule(
            "t.create",
            type="strds",
            temporaltype="absolute",
            output=cls.strds_name,
            title="Test kappa STRDS",
            description="Test kappa STRDS dataset",
            overwrite=True,
        )
        cls.runModule(
            "t.register",
            flags="i",
            type="raster",
            input=cls.strds_name,
            maps=",".join(cls.map_names),
            start="2001-01-01",
            increment="1 year",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "t.remove",
            flags="rf",
            type="strds",
            inputs=cls.strds_name,
        )

    def test_pairwise_rkappa(self):
        """Test pairwise kappa analysis using r.kappa backend (-k flag)."""
        output_path = os.path.join(tempfile.gettempdir(), "test_kappa_out.txt")
        try:
            if os.path.exists(output_path):
                os.remove(output_path)
            self.assertModule(
                "t.rast.kappa",
                flags="k",
                strds=self.strds_name,
                output=output_path,
            )
        finally:
            if os.path.exists(output_path):
                os.remove(output_path)

    def test_pixel_by_pixel_split(self):
        """Test pixel-by-pixel analysis with splittingday (-p flag)."""
        output_raster = "test_pixel_kappa_result"
        try:
            self.assertModule(
                "t.rast.kappa",
                flags="p",
                strds=self.strds_name,
                splittingday="2002-06-01",
                output=output_raster,
                overwrite=True,
            )
            self.assertRasterExists(output_raster)
        finally:
            self.runModule("g.remove", flags="f", type="raster", name=[output_raster])

    def test_invalid_flag_combinations(self):
        """Test that incompatible flags (-k and -p) fail properly."""
        self.assertModuleFail(
            "t.rast.kappa",
            flags="kp",
            strds=self.strds_name,
            splittingday="2002-06-01",
            output="test_fail",
        )

    def test_p_flag_without_splittingday_fails(self):
        """Test that -p flag without splittingday fails."""
        self.assertModuleFail(
            "t.rast.kappa",
            flags="p",
            strds=self.strds_name,
            output="test_fail",
        )


if __name__ == "__main__":
    test()
