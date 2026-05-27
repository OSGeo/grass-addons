"""Tests for r.richdem.flowaccum

Synthetic DEM (5 x 5, 1 m resolution) — uniform south-facing slope:

    5 5 5 5 5   (row 1, north)
    4 4 4 4 4
    3 3 3 3 3
    2 2 2 2 2
    1 1 1 1 1   (row 5, south)

No depressions or flat areas; all cells drain unambiguously southward.

D8 flow-accumulation properties for this DEM:
  - All 16 border cells drain directly off the edge — each has FA = 1.
  - Interior cells accumulate drainage from cells to their north.
  - min FA = 1 (border cells); max FA = 4 (most-accumulated interior cell).
  - No null cells (every cell has a valid accumulation value).
"""

import unittest

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

try:
    import _richdem  # noqa: F401

    HAS_RICHDEM = True
except ImportError:
    HAS_RICHDEM = False

_DEM = "tmp_richdem_flowaccum_dem"
_FA_D8 = "tmp_richdem_flowaccum_d8"
_FA_DINF = "tmp_richdem_flowaccum_dinf"

# Uniform south-facing slope: row 1 (north) = 5, row 5 (south) = 1
_DEM_EXPR = "6 - row()"


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemFlowaccum(TestCase):
    """Functional tests for r.richdem.flowaccum requiring the RichDEM extension."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=0, e=5, w=0, res=1)
        cls.runModule(
            "r.mapcalc", expression=f"{_DEM} = {_DEM_EXPR}", overwrite=True
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[_DEM, _FA_D8, _FA_DINF],
        )

    def test_output_created(self):
        """D8 flow accumulation produces an output raster."""
        self.assertModule(
            "r.richdem.flowaccum",
            input=_DEM,
            output=_FA_D8,
            method="D8",
            overwrite=True,
        )
        self.assertRasterExists(_FA_D8)

    def test_min_is_one(self):
        """Minimum flow accumulation is 1 — every cell counts at least itself."""
        self.runModule(
            "r.richdem.flowaccum",
            input=_DEM,
            output=_FA_D8,
            method="D8",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_FA_D8, flags="g")
        self.assertAlmostEqual(
            float(stats["min"]),
            1.0,
            places=5,
            msg="Minimum FA is not 1; border cells should count only themselves",
        )

    def test_accumulation_occurs(self):
        """Maximum FA exceeds 1 — interior cells accumulate upstream drainage."""
        self.runModule(
            "r.richdem.flowaccum",
            input=_DEM,
            output=_FA_D8,
            method="D8",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_FA_D8, flags="g")
        self.assertGreater(
            float(stats["max"]),
            1.0,
            msg="Maximum FA is not > 1; no upstream accumulation was detected",
        )

    def test_no_null_cells(self):
        """Every cell has a valid (non-null) flow accumulation value."""
        self.runModule(
            "r.richdem.flowaccum",
            input=_DEM,
            output=_FA_D8,
            method="D8",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_FA_D8, flags="g")
        self.assertEqual(
            int(stats["null_cells"]),
            0,
            msg="Null cells found in flow accumulation output",
        )

    def test_dinf_method(self):
        """D-infinity (Tarboton) method produces an output raster."""
        self.assertModule(
            "r.richdem.flowaccum",
            input=_DEM,
            output=_FA_DINF,
            method="Dinf",
            overwrite=True,
        )
        self.assertRasterExists(_FA_DINF)


if __name__ == "__main__":
    test()
