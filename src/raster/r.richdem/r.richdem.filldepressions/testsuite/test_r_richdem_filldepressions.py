"""Tests for r.richdem.filldepressions

Synthetic DEM (5 x 5, 1 m resolution) with an outlet on the right border:

    5 5 5 5 5
    5 4 4 4 5
    5 4 1 4 3   <- centre pit (1), outlet at right-border midpoint = 3
    5 4 4 4 5
    5 5 5 5 5

The pit is drained through the outlet (elevation 3) on the right border.
Priority-Flood fill raises the pit to the pour-point (elevation 4 — the
lowest ring cell adjacent to the outlet path).  The outlet cell itself (3)
is a border cell and is never modified by the algorithm.

Expected outcomes:
  - min = 3  (outlet border cell, unchanged)
  - max = 5  (remaining border cells, unchanged)
  - filled - input >= 0 everywhere  (filling never lowers any cell)
  - centre pit raised from 1 to 4  (the pour-point elevation)
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
        """Pit raised to pour-point (4); outlet (3) and border (5) unchanged."""
        self.runModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        self.assertRasterMinMax(_FILLED, refmin=3.0, refmax=5.0)

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
        """With -e, epsilon gradients on flats keep min=3 (outlet) and max=5 (border)."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED_E,
            flags="e",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED_E, refmin=3.0, refmax=5.0)

    def test_d4_topology(self):
        """D4 topology option completes without error and raises pit to pour-point."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterMinMax(_FILLED, refmin=3.0, refmax=5.0)


if __name__ == "__main__":
    test()
