"""Tests for r.richdem.filldepressions

Synthetic DEM (5 x 5, 1 m resolution):

    5 5 5 5 5
    5 3 3 3 5
    5 3 1 3 5   <- centre pit, elevation 1
    5 3 3 3 5
    5 5 5 5 5

The entire inner 3 x 3 drains toward the centre pit.  The pour-point
elevation is 3 (the lowest rim cell).  After complete filling, the pit
rises from 1 to 3; all other cells are unchanged.
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

# 5x5: border=5, inner ring=3, centre=1
_DEM_EXPR = (
    "if(row()==3 && col()==3, 1,"
    " if(row()==1 || row()==5 || col()==1 || col()==5, 5, 3))"
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
        cls.runModule("r.mapcalc", expression=f"{_DEM} = {_DEM_EXPR}", overwrite=True)

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
        """Pit cell is raised to the pour-point elevation (3); max unchanged (5)."""
        self.runModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        self.assertRasterMinMax(_FILLED, refmin=3.0, refmax=5.0)

    def test_fill_never_lowers(self):
        """No cell in the filled DEM has a lower elevation than the input."""
        # Use assertModule so a module failure surfaces immediately, not as a
        # confusing null-cell artifact in the diff raster.
        self.assertModule(
            "r.richdem.filldepressions", input=_DEM, output=_FILLED, overwrite=True
        )
        diff = "tmp_richdem_fill_diff"
        # filled - input should be >= 0 everywhere (filling only raises cells)
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

    def test_epsilon_flag_removes_flats(self):
        """With -e, the filled output has no value strictly below the pour point."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED_E,
            flags="e",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_FILLED_E, flags="g")
        self.assertGreaterEqual(
            float(stats["min"]),
            3.0,
            msg="Epsilon-filled DEM has a cell below the pour-point elevation",
        )

    def test_d4_topology(self):
        """D4 topology option completes without error and produces output."""
        self.assertModule(
            "r.richdem.filldepressions",
            input=_DEM,
            output=_FILLED,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterExists(_FILLED)


if __name__ == "__main__":
    test()
