"""Tests for r.richdem.resolveflats

Synthetic DEM (5 x 5, 1 m resolution) with a flat interior:

    5 5 5 5 5
    5 3 3 3 5
    5 3 3 3 5   <- inner 3x3 all at elevation 3 (a flat)
    5 3 3 3 5
    5 5 5 5 5

ResolveFlats (Barnes et al., 2014b) adds sub-epsilon gradient adjustments
to flat cells to guide flow routing.  The adjustments are on the order of
the floating-point epsilon relative to the cell elevation and are not
representable as distinct values in the output DCELL raster.  Observable
outcomes are therefore conservative:

  - The output raster is created with no null cells.
  - The min and max elevations are unchanged (3 and 5 respectively).
  - The module completes without error.
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

_DEM = "tmp_richdem_resolveflats_dem"
_RESOLVED = "tmp_richdem_resolveflats_out"

# Border=5, inner flat=3; no pit
_DEM_EXPR = "if(row()==1 || row()==5 || col()==1 || col()==5, 5, 3)"


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemResolveFlats(TestCase):
    """Functional tests for r.richdem.resolveflats requiring the RichDEM extension."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=0, e=5, w=0, res=1)
        cls.runModule("r.mapcalc", expression=f"{_DEM} = {_DEM_EXPR}", overwrite=True)

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[_DEM, _RESOLVED],
        )

    def test_output_created(self):
        """Resolving flats produces an output raster without error."""
        self.assertModule(
            "r.richdem.resolveflats", input=_DEM, output=_RESOLVED, overwrite=True
        )
        self.assertRasterExists(_RESOLVED)

    def test_no_nulls_introduced(self):
        """Output has no null cells (same valid-cell count as input)."""
        self.runModule(
            "r.richdem.resolveflats", input=_DEM, output=_RESOLVED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_RESOLVED, flags="g")
        self.assertEqual(
            int(stats["null_cells"]),
            0,
            msg="Null cells were introduced by resolveflats",
        )

    def test_min_unchanged(self):
        """Minimum elevation is not lowered (flat inner cells stay at 3)."""
        self.runModule(
            "r.richdem.resolveflats", input=_DEM, output=_RESOLVED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_RESOLVED, flags="g")
        self.assertAlmostEqual(
            float(stats["min"]),
            3.0,
            places=5,
            msg="Minimum elevation changed; resolveflats should not lower cells",
        )

    def test_max_unchanged(self):
        """Maximum elevation is not raised (border cells stay at 5)."""
        self.runModule(
            "r.richdem.resolveflats", input=_DEM, output=_RESOLVED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_RESOLVED, flags="g")
        self.assertAlmostEqual(
            float(stats["max"]),
            5.0,
            places=5,
            msg="Maximum elevation changed; border cells should be untouched",
        )


if __name__ == "__main__":
    test()
