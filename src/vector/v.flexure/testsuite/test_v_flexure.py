#!/usr/bin/env python

############################################################################
#
# MODULE:       test_v_flexure
# AUTHOR:       Andrew Wickert
# PURPOSE:      Tests for v.flexure (point-load flexural isostasy)
# COPYRIGHT:    (C) 2026 by Andrew Wickert and the GRASS Development Team
#
#               This program is free software under the GNU General Public
#               License (>=v2). Read the file COPYING that comes with GRASS
#               for details.
#
############################################################################

"""
Tests for v.flexure.

Creates a synthetic single-point load vector (no NC dataset required) and
exercises the SAS_NG solver with scalar Te values. Skips automatically when
gFlex >= 2.0.0 is not installed.

Run inside a GRASS session (e.g., with --tmp-location XY):
    python -m grass.gunittest.main
"""

import unittest

import grass.script as grass
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


def _gflex_ok():
    """Return True if gFlex is importable."""
    try:
        import gflex  # noqa: F401

        return True
    except ImportError:
        return False


@unittest.skipUnless(_gflex_ok(), "gFlex not available")
class TestVFlexure(TestCase):
    """Test v.flexure with a synthetic single-point load (no NC dataset required)."""

    loads = "test_vflex_loads"
    output = "test_vflex_rout"

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        # 10×10 grid at 100 m resolution (1 km × 1 km)
        cls.runModule("g.region", n=1000, s=0, e=1000, w=0, res=100)
        # Single point at domain center (500, 500), loaded as a point force [N]
        cls.runModule(
            "v.in.ascii",
            format="point",
            input="-",
            stdin_="500 500",
            separator="space",
            output=cls.loads,
        )
        cls.runModule("v.db.addtable", map=cls.loads)
        cls.runModule(
            "v.db.addcolumn",
            map=cls.loads,
            columns="q double precision",
        )
        cls.runModule(
            "v.db.update",
            map=cls.loads,
            column="q",
            value="1e15",
            where="cat=1",
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove", flags="f", type="vector", name=cls.loads, quiet=True
        )

    def tearDown(self):
        self.runModule(
            "g.remove", flags="f", type="raster", name=self.output, quiet=True
        )

    def test_basic_deflection(self):
        """SAS_NG solver produces a valid raster output."""
        self.assertModule(
            "v.flexure",
            input=self.loads,
            column="q",
            te="10000",
            te_units="m",
            output=self.output,
        )
        self.assertRasterExists(self.output)
        self.assertRasterFitsUnivar(
            raster=self.output, reference={"n": 100}, precision=0
        )
        stats = grass.parse_command("r.univar", map=self.output, flags="g")
        min_w = float(stats["min"])
        self.assertLess(min_w, 0,
                        "Deflection under a downward load must be negative")
        self.assertGreater(min_w, -1000,
                           "Deflection magnitude must be physically plausible (< 1 km)")

    def test_w_points_output(self):
        """w_points writes deflection values into an existing vector map."""
        w_pts = "test_vflex_wpts"
        try:
            # Create a small set of arbitrary evaluation points
            self.runModule(
                "v.in.ascii",
                format="point",
                input="-",
                stdin_="200 200\n500 500\n800 800",
                separator="space",
                output=w_pts,
            )
            self.runModule("v.db.addtable", map=w_pts)
            self.assertModule(
                "v.flexure",
                input=self.loads,
                column="q",
                te="10000",
                te_units="m",
                output=self.output,
                w_points=w_pts,
            )
            self.assertRasterExists(self.output)
            # The w column should now exist and be populated
            db = grass.vector_db_select(w_pts)
            col_lower = [c.lower() for c in db["columns"]]
            self.assertIn("w", col_lower,
                          "w column should be present in w_points map")
            w_idx = col_lower.index("w")
            w_vals = [float(row[w_idx]) for row in db["values"].values()]
            self.assertTrue(any(v < 0 for v in w_vals),
                            "At least one deflection value should be negative")
        finally:
            self.runModule(
                "g.remove", flags="f", type="vector", name=w_pts, quiet=True
            )

    def test_w_points_custom_column(self):
        """w_column parameter controls the name of the written column."""
        w_pts = "test_vflex_wpts_col"
        try:
            self.runModule(
                "v.in.ascii",
                format="point",
                input="-",
                stdin_="500 500",
                separator="space",
                output=w_pts,
            )
            self.runModule("v.db.addtable", map=w_pts)
            self.assertModule(
                "v.flexure",
                input=self.loads,
                column="q",
                te="10000",
                te_units="m",
                output=self.output,
                w_points=w_pts,
                w_column="deflection",
            )
            db = grass.vector_db_select(w_pts)
            self.assertIn("deflection", [c.lower() for c in db["columns"]],
                          "deflection column should be present in w_points map")
        finally:
            self.runModule(
                "g.remove", flags="f", type="vector", name=w_pts, quiet=True
            )

    def test_te_km_units(self):
        """Te in km produces output without error."""
        self.assertModule(
            "v.flexure",
            input=self.loads,
            column="q",
            te="10",
            te_units="km",
            output=self.output,
        )
        self.assertRasterExists(self.output)

    def test_custom_material_params(self):
        """Non-default Young's modulus and mantle density are accepted."""
        self.assertModule(
            "v.flexure",
            input=self.loads,
            column="q",
            te="10000",
            te_units="m",
            output=self.output,
            ym="70E9",
            rho_m="3200",
        )
        self.assertRasterExists(self.output)

    def test_te_km_m_equivalence(self):
        """Te=10 km and Te=10000 m must produce identical deflections.

        Interface-layer test: verifies that the km→m conversion (Te *= 1000)
        is applied correctly.
        """
        out_km = "test_vflex_te_km"
        out_m = "test_vflex_te_m"
        try:
            self.assertModule(
                "v.flexure", input=self.loads, column="q",
                te="10", te_units="km", output=out_km,
            )
            self.assertModule(
                "v.flexure", input=self.loads, column="q",
                te="10000", te_units="m", output=out_m,
            )
            stats_km = grass.parse_command("r.univar", map=out_km, flags="g")
            stats_m = grass.parse_command("r.univar", map=out_m, flags="g")
            self.assertAlmostEqual(
                float(stats_km["min"]), float(stats_m["min"]), places=10,
                msg="Te in km and m must give identical min deflection",
            )
        finally:
            self.runModule(
                "g.remove", flags="f", type="raster",
                name=",".join([out_km, out_m]), quiet=True,
            )

    def test_deflection_decays_with_distance(self):
        """Deflection magnitude decreases with distance from the load point.

        The load is at the domain centre (500, 500).  The minimum deflection
        (peak subsidence, most negative) must be more negative than the mean,
        which is pulled toward zero by cells far from the load.
        """
        self.assertModule(
            "v.flexure",
            input=self.loads,
            column="q",
            te="10000",
            te_units="m",
            output=self.output,
        )
        stats = grass.parse_command("r.univar", map=self.output, flags="g")
        min_w = float(stats["min"])
        mean_w = float(stats["mean"])
        self.assertLess(
            min_w, mean_w,
            "Peak subsidence at load centre must exceed mean deflection",
        )
        self.assertLess(mean_w, 0, "Mean deflection must be negative")

    def test_multi_point_loads(self):
        """Two load points are processed correctly; exercises the SQL attribute loop."""
        loads2 = "test_vflex_loads2"
        output2 = "test_vflex_rout2"
        try:
            self.runModule(
                "v.in.ascii",
                format="point",
                input="-",
                stdin_="400 400\n600 600",
                separator="space",
                output=loads2,
            )
            self.runModule("v.db.addtable", map=loads2)
            self.runModule(
                "v.db.addcolumn", map=loads2, columns="q double precision"
            )
            self.runModule(
                "v.db.update", map=loads2, column="q", value="1e15", where="cat=1"
            )
            self.runModule(
                "v.db.update", map=loads2, column="q", value="8e14", where="cat=2"
            )
            self.assertModule(
                "v.flexure",
                input=loads2,
                column="q",
                te="10000",
                te_units="m",
                output=output2,
            )
            self.assertRasterExists(output2)
        finally:
            self.runModule(
                "g.remove", flags="f", type="vector", name=loads2, quiet=True
            )
            self.runModule(
                "g.remove", flags="f", type="raster", name=output2, quiet=True
            )


if __name__ == "__main__":
    test()
