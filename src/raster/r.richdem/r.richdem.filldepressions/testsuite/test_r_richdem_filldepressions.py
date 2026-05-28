"""Tests for r.richdem.filldepressions

Synthetic DEM (5 x 5, 1 m resolution) with a low saddle adjacent to the
right border:

    5 5 5 5 5
    5 9 9 9 5
    5 9 1 4 5   <- pit=1, saddle=4 immediately left of right border (5)
    5 9 9 9 5
    5 5 5 5 5

The pit (1) is enclosed by the outer ring (9) except for the saddle (4) at
(row=3, col=4), which is directly adjacent to the right border (5).
Priority-Flood fill raises both the pit and the saddle to the pour-point
(= border elevation = 5, since the saddle connects directly to the border).
The ring (9) and border (5) cells are never lowered.

Expected outcomes:
  - min = 5.0  (pit and saddle raised to pour-point; border unchanged)
  - max = 9.0  (ring cells unchanged)
  - filled - input >= 0 everywhere  (filling never lowers any cell)

This DEM is shared with r.richdem.breachdepressions tests so that all three
algorithms produce distinct, directly comparable results on the same input:
  fill              => min == 5.0  (everything raised to pour-point)
  CompleteBreaching => min == 4.0  (pit raised to saddle; saddle preserved)
  Lindsay2016 eps   => min <  4.0  (pit shallowed to just below saddle)
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

# 5x5: border=5, outer ring=9, centre pit=1, saddle at (row=3,col=4)=4.
# The saddle is the pit's lowest neighbour and sits directly adjacent to the
# right border, making the pour-point unambiguously the border elevation (5).
_DEM_EXPR = (
    "if(row()==3 && col()==3, 1,"
    " if(row()==3 && col()==4, 4,"
    " if(row()==1 || row()==5 || col()==1 || col()==5, 5, 9)))"
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

    def test_fill_raises_to_pour_point(self):
        """Pit and saddle raised to pour-point (5); ring (9) and border (5) unchanged."""
        self.runModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        self.assertRasterMinMax(_FILLED, refmin=5.0, refmax=9.0)

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

    def test_epsilon_flag_preserves_range(self):
        """With -e, epsilon gradients on flats keep min=5 (pour-point) and max=9 (ring)."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED_E,
            flags="e",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED_E, refmin=5.0, refmax=9.0)

    def test_d4_topology(self):
        """D4 topology option completes without error and raises pit to pour-point."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED, refmin=5.0, refmax=9.0)


if __name__ == "__main__":
    test()
