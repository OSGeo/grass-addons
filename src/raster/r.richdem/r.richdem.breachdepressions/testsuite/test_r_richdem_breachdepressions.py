"""Tests for r.richdem.breachdepressions

Synthetic DEM (5 x 5, 1 m resolution):

    5 5 5 5 5
    5 3 3 3 5
    5 3 1 3 5   <- centre pit, elevation 1
    5 3 3 3 5
    5 5 5 5 5

Breaching proceeds in two relevant phases for this DEM:

  1. Pit shallowing: the centre pit (elevation 1) is raised to just below
     its lowest neighbour (elevation 3), giving ~2.999...

  2. Priority-flood breach: the path from the shallowed pit to the border
     (5 → 3 → ~2.999) is already monotonically descending, so no ring cell
     needs to be lowered.

Observable outcomes:
  - Max elevation is 5 (border cells are never modified).
  - Min elevation is above the original pit value of 1 (shallowing raised it).
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

_DEM_EXPR = (
    f"if(row()==3 && col()==3, 1,"
    f" if(row()==1 || row()==5 || col()==1 || col()==5, 5, 3))"
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

    def test_max_unchanged(self):
        """Border cells (maximum elevation 5) are never modified by breaching."""
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertAlmostEqual(
            float(stats["max"]),
            5.0,
            places=5,
            msg="Maximum elevation changed; border cells should be untouched",
        )

    def test_pit_raised_above_input(self):
        """Pit shallowing raises the centre cell above its input elevation of 1.

        Phase 1 of the breach algorithm raises each pit to just below its
        lowest neighbour, so the minimum of the breached DEM must exceed the
        original pit elevation (1).
        """
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertGreater(
            float(stats["min"]),
            1.0,
            msg="Min of breached DEM is not above 1; pit shallowing may not have run",
        )

    def test_d4_topology(self):
        """D4 topology option completes without error and produces output."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_D4,
            topology="D4",
            overwrite=True,
        )
        self.assertRasterExists(_BREACHED_D4)


if __name__ == "__main__":
    test()
