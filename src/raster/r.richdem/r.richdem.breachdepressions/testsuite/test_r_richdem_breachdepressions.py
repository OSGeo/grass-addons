"""Tests for r.richdem.breachdepressions

Synthetic DEM (5 x 5, 1 m resolution) with a low saddle adjacent to the
right border:

    5 5 5 5 5
    5 9 9 9 5
    5 9 1 4 5   <- pit=1, saddle=4 immediately left of right border (5)
    5 9 9 9 5
    5 5 5 5 5

The pit (1) is enclosed by the outer ring (9) except for the saddle (4) at
(row=3, col=4), which is directly adjacent to the right border (5).

This DEM is shared with r.richdem.filldepressions tests so that all three
algorithms produce distinct, directly comparable results on the same input:

  fill              => min == 5.0  (pit and saddle raised to pour-point 5)
  CompleteBreaching => min == 4.0  (pit raised to saddle; saddle preserved)
  Lindsay2016 eps   => min <  4.0  (pit shallowed to just below saddle)

CompleteBreaching (TestRichdemBreach):
  `rd.BreachDepressions` calls `CompleteBreaching_Lindsay2016`, which raises
  the pit to `lowest_neighbour` (= saddle = 4), sets target_height = 4, then
  walks the backlink path (pit -> saddle -> border) lowering every cell whose
  elevation >= target_height to target_height.  The saddle (4) is unchanged;
  the border cell (5) is lowered to 4.
  Result: pit=4, saddle=4, ring=9, border(3,5)=4.  min=4, max=9.

Lindsay2016 eps (TestRichdemBreachEps, skipped unless BreachDepressionsEps
  is available):
  `rd.BreachDepressionsEps` calls `Lindsay2016` with `eps_gradients=True`,
  which uses `std::nextafter` to shallow the pit to just BELOW
  `lowest_neighbour` (~3.9999...) rather than exactly to it.
  Result: pit ~= 3.9999, saddle=4, ring=9, border=5.  min < 4.0.
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

HAS_LINDSAY2016 = False
if HAS_RICHDEM:
    try:
        import richdem as _rd

        HAS_LINDSAY2016 = hasattr(_rd, "BreachDepressionsEps")
    except ImportError:
        pass

_DEM = "tmp_richdem_breach_dem"
_BREACHED = "tmp_richdem_breach_out"
_BREACHED_D4 = "tmp_richdem_breach_out_d4"
_BREACHED_EPS = "tmp_richdem_breach_out_eps"

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
class TestRichdemBreach(TestCase):
    """Tests for CompleteBreaching_Lindsay2016 (rd.BreachDepressions)."""

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
            name=[_DEM, _BREACHED, _BREACHED_D4],
        )

    def test_output_created(self):
        """Breaching a DEM with one depression produces an output raster."""
        self.assertModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        self.assertRasterExists(_BREACHED)

    def test_pit_raised_to_saddle(self):
        """Pit raised to saddle (4); ring (9) and border (5) unchanged; min=4, max=9."""
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        self.assertRasterMinMax(_BREACHED, refmin=4.0, refmax=9.0)

    def test_breach_below_pour_point(self):
        """CompleteBreaching leaves min (4.0) below the fill pour-point (5.0).

        Fill raises pit and saddle to the border elevation (5); breach raises
        the pit only to the saddle elevation (4) and preserves the saddle.
        """
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertLess(
            float(stats["min"]),
            5.0,
            msg="min of breached DEM >= 5.0; pit was raised to pour-point (fill behaviour)",
        )

    def test_d4_topology(self):
        """D4 topology completes without error; pit raised to saddle (min=4, max=9)."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_D4,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterMinMax(_BREACHED_D4, refmin=4.0, refmax=9.0)


@unittest.skipUnless(
    HAS_LINDSAY2016,
    "BreachDepressionsEps not available in this RichDEM build; "
    "a patch exposing Lindsay2016 eps_gradients via the Python bindings is needed upstream",
)
class TestRichdemBreachEps(TestCase):
    """Tests for Lindsay2016 epsilon-gradient breaching (rd.BreachDepressionsEps, -e flag).

    Skipped unless the upstream RichDEM Python bindings expose BreachDepressionsEps.
    """

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
            name=[_DEM, _BREACHED_EPS],
        )

    def test_output_created(self):
        """Lindsay2016 eps breaching produces an output raster."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_EPS,
            flags="e",
            overwrite=True,
        )
        self.assertRasterExists(_BREACHED_EPS)

    def test_epsilon_shallows_below_saddle(self):
        """Lindsay2016 eps shallows pit to just below saddle (min < 4.0).

        Unlike CompleteBreaching (min == 4.0), eps_gradients uses
        std::nextafter to raise the pit to nextafter(4.0, -inf) ~= 3.9999,
        leaving it strictly below the saddle elevation.
        """
        self.runModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_EPS,
            flags="e",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_BREACHED_EPS, flags="g")
        self.assertLess(
            float(stats["min"]),
            4.0,
            msg="min of eps-breached DEM >= 4.0; pit was not shallowed below saddle",
        )

    def test_d4_topology(self):
        """D4 topology with -e completes without error and shallows pit below saddle."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_EPS,
            flags="e",
            topology="D4",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_BREACHED_EPS, flags="g")
        self.assertLess(float(stats["min"]), 4.0)


if __name__ == "__main__":
    test()
