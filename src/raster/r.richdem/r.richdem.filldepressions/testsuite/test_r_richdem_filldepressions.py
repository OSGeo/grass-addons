"""Tests for r.richdem.filldepressions

Synthetic DEM (5 x 5, 1 m resolution) with a closed rim:

    5 5 5 5 5
    5 4 4 4 5
    5 4 1 4 5   <- centre pit (1) surrounded by uniform rim at elevation 4
    5 4 4 4 5
    5 5 5 5 5

The pit is completely enclosed: the only drainage outlet is over the rim
at elevation 4.  After filling, the pit and all inner cells rise to the
pour-point elevation (4); the border cells (5) are unchanged.

Expected outcomes:
  - min of filled DEM = 4.0  (pit raised to pour-point)
  - max of filled DEM = 5.0  (border cells unchanged)
  - filled - input >= 0 everywhere  (filling never lowers)

This DEM is intentionally different from the breach-depressions test so
that the two algorithms produce distinct, verifiable results:
  - fill  => min == 4.0  (entire interior raised to rim level)
  - breach => min <  4.0  (pit shallowed but not raised to rim; channel cut)
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

_DEM = "tmp_richdem_fill_dem"
_FILLED = "tmp_richdem_fill_out"
_FILLED_E = "tmp_richdem_fill_out_e"

# 5x5: border=5, rim=4, centre pit=1
_DEM_EXPR = (
    "if(row()==1 || row()==5 || col()==1 || col()==5, 5,"
    " if(row()==3 && col()==3, 1, 4))"
)


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemFill(TestCase):
    """Functional tests for r.richdem.filldepressions requiring the RichDEM extension."""

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
            name=[_DEM, _FILLED, _FILLED_E],
        )

    def test_output_created(self):
        """Filling a DEM with one depression produces an output raster."""
        self.assertModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        self.assertRasterExists(_FILLED)

    def test_fill_raises_pit_to_pour_point(self):
        """Pit is raised to the pour-point elevation (4); border stays at 5."""
        self.runModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        self.assertRasterMinMax(_FILLED, refmin=4.0, refmax=5.0)

    def test_fill_never_lowers(self):
        """No cell in the filled DEM has a lower elevation than the input."""
        self.runModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        diff = "tmp_richdem_fill_diff"
        self.runModule(
            "r.mapcalc",
            expression=f"{diff} = {_FILLED} - {_DEM}",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=diff, flags="g")
        self.runModule("g.remove", flags="f", type="raster", name=diff)
        self.assertGreaterEqual(
            float(stats["min"]),
            0.0,
            msg="At least one cell was lowered by filling (min of filled-input < 0)",
        )

    def test_epsilon_flag_preserves_min(self):
        """With -e, epsilon gradients are imposed on flats but min stays at pour-point."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED_E,
            flags="e",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED_E, refmin=4.0, refmax=5.0)

    def test_d4_topology(self):
        """D4 topology option completes without error and raises pit to pour-point."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED, refmin=4.0, refmax=5.0)


if __name__ == "__main__":
    test()
