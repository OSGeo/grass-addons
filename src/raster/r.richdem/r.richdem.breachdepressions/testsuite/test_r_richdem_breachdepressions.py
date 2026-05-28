"""Tests for r.richdem.breachdepressions

Synthetic DEM (5 x 5, 1 m resolution) with an outlet on the right border:

    5 5 5 5 5
    5 4 4 4 5
    5 4 1 4 3   <- centre pit (1), outlet at right-border midpoint = 3
    5 4 4 4 5
    5 5 5 5 5

`r.richdem.breachdepressions` calls RichDEM's `CompleteBreaching_Lindsay2016`.
For this simple single-depression DEM:

  1. Pit shallowing: the centre pit (elevation 1) is raised to the lowest
     neighbour (elevation 4).

  2. Priority-flood breach carving: the backlink path from the pit to the
     border passes through ring cells already at elevation 4 and the outlet
     cell at elevation 3.  No cell on this path is above the target height
     (4), so the carving pass makes no changes.

The result is numerically identical to Priority-Flood fill for this DEM:
both algorithms set the pit to the pour-point (4) and leave the outlet (3)
and border (5) unchanged.  A more complex DEM with a ridge above the
pour-point on the breach path would produce distinct results.

Observable outcomes:
  - max = 5.0  (border cells are never modified)
  - min = 3.0  (outlet border cell unchanged; pit raised to 4)
  - min > 1.0  (pit was shallowed above its original elevation of 1)
  - breached - input >= 0 everywhere  (breaching never lowers any cell)
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

_DEM = "tmp_richdem_breach_dem"
_BREACHED = "tmp_richdem_breach_out"
_BREACHED_D4 = "tmp_richdem_breach_out_d4"

# 5x5: border=5, inner ring=4, centre pit=1, outlet at (row=3,col=5)=3
# The outlet must be tested first because (row=3,col=5) is also a border cell.
_DEM_EXPR = (
    "if(row()==3 && col()==5, 3,"
    " if(row()==1 || row()==5 || col()==1 || col()==5, 5,"
    " if(row()==3 && col()==3, 1, 4)))"
)


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemBreach(TestCase):
    """Functional tests for r.richdem.breachdepressions requiring the RichDEM extension."""

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

    def test_border_and_outlet_unchanged(self):
        """Border cells (5) and outlet cell (3) are preserved; max=5, min=3."""
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        self.assertRasterMinMax(_BREACHED, refmin=3.0, refmax=5.0)

    def test_pit_raised_above_original(self):
        """Centre pit (elevation 1) is raised above its original elevation.

        After breaching, the pit is shallowed to the pour-point (4).  The new
        minimum is the outlet cell (3), which is > 1, confirming that the pit
        was processed and is no longer the global minimum.
        """
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertGreater(
            float(stats["min"]),
            1.0,
            msg="min of breached DEM is not above 1; pit shallowing did not run",
        )

    def test_never_lowers(self):
        """No cell in the breached DEM has a lower elevation than the input."""
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        diff = "tmp_richdem_breach_diff"
        self.runModule(
            "r.mapcalc",
            expression=f"{diff} = {_BREACHED} - {_DEM}",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=diff, flags="g")
        self.runModule("g.remove", flags="f", type="raster", name=diff)
        self.assertGreaterEqual(
            float(stats["min"]),
            0.0,
            msg="At least one cell was lowered by breaching (min of breached-input < 0)",
        )

    def test_d4_topology(self):
        """D4 topology completes without error and preserves border and outlet."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_D4,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterMinMax(_BREACHED_D4, refmin=3.0, refmax=5.0)


if __name__ == "__main__":
    test()
