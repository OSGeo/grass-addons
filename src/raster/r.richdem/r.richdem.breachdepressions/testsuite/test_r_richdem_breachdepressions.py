"""Tests for r.richdem.breachdepressions

Synthetic DEM (5 x 5, 1 m resolution) with a closed rim:

    5 5 5 5 5
    5 4 4 4 5
    5 4 1 4 5   <- centre pit (1) surrounded by uniform rim at elevation 4
    5 4 4 4 5
    5 5 5 5 5

The pit is completely enclosed.  The breach algorithm operates in two phases:

  1. Pit shallowing: the centre pit (elevation 1) is raised to just below its
     lowest neighbour (elevation 4), yielding ~3.999... (4 - float epsilon).

  2. Priority-flood breach: the shallowed pit (~3.999) is lower than the rim
     (4), so the algorithm lowers one rim cell to form a monotonically
     descending channel from pit to border.

Observable outcomes:
  - max = 5.0  (border cells are never modified)
  - min > 1.0  (pit was shallowed above its original elevation)
  - min < 4.0  (pit and/or channel cell sit below the rim — NOT raised to it)

The third assertion is the critical one that distinguishes breaching from
filling: filling would set min = 4.0 (raises to pour-point); breaching leaves
min < 4.0 (cuts a channel without raising the interior to the rim).
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

    def test_border_unchanged(self):
        """Border cells (elevation 5) are never modified by breaching."""
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

    def test_pit_shallowed_above_original(self):
        """Pit shallowing raises the centre cell above its original elevation (1)."""
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertGreater(
            float(stats["min"]),
            1.0,
            msg="Min of breached DEM is not above 1; pit shallowing did not run",
        )

    def test_channel_cut_below_rim(self):
        """Breaching cuts a channel below the rim (min < 4.0), unlike filling.

        Filling raises the entire interior to the pour-point (min = 4.0).
        Breaching shallows the pit to just below the rim (~3.999) and cuts one
        rim cell, so min must be strictly less than 4.0.
        """
        self.runModule(
            "r.richdem.breachdepressions", input=_DEM, output=_BREACHED, overwrite=True
        )
        stats = gs.parse_command("r.univar", map=_BREACHED, flags="g")
        self.assertLess(
            float(stats["min"]),
            4.0,
            msg="Min of breached DEM is >= 4.0; interior was raised to rim level "
                "(filling behaviour), not breached",
        )

    def test_d4_topology(self):
        """D4 topology completes without error and also cuts channel below rim."""
        self.assertModule(
            "r.richdem.breachdepressions",
            input=_DEM,
            output=_BREACHED_D4,
            topology="D4",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_BREACHED_D4, flags="g")
        self.assertLess(
            float(stats["min"]),
            4.0,
            msg="D4 breach min >= 4.0; channel was not cut below the rim",
        )


if __name__ == "__main__":
    test()
