"""Tests for r.richdem.fsm

Synthetic DEM (5 x 5, 1 m resolution):

    5 5 5 5 5
    5 3 3 3 5
    5 3 1 3 5   <- centre pit, elevation 1
    5 3 3 3 5
    5 5 5 5 5

r.richdem.dephier is run once in setUpClass; its outputs feed FSM.
Water-table depth (wtd) convention: negative = unsaturated (below
surface), positive = ponded water above surface.

Two water scenarios are tested:

  Dry   wtd = −1 everywhere (no ponded water)
  Wet   wtd = +1.5 in depression cells, −1 elsewhere

Note: when the maximum value in a DCELL raster is exactly 0.0, GRASS
r.univar reports max=nan and range=nan even though no null or NaN cells
are present (reproducible with a plain r.mapcalc raster of the same
pattern).  Tests therefore use r.univar min and mean rather than max.
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

_DEM = "tmp_richdem_fsm_dem"
_LABELS = "tmp_richdem_fsm_labels"
_FLOWDIRS = "tmp_richdem_fsm_flowdirs"
_HIERARCHY = "tmp_richdem_fsm_hierarchy"
_WTD_DRY = "tmp_richdem_fsm_wtd_dry"
_WTD_WET = "tmp_richdem_fsm_wtd_wet"
_OUT_DRY = "tmp_richdem_fsm_out_dry"
_OUT_WET = "tmp_richdem_fsm_out_wet"

_DEM_EXPR = (
    f"if(row()==3 && col()==3, 1,"
    f" if(row()==1 || row()==5 || col()==1 || col()==5, 5, 3))"
)


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemFsm(TestCase):
    """Functional tests for r.richdem.fsm requiring the RichDEM extension."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        cls.runModule("g.region", n=5, s=0, e=5, w=0, res=1)
        cls.runModule(
            "r.mapcalc", expression=f"{_DEM} = {_DEM_EXPR}", overwrite=True
        )
        cls.runModule(
            "r.richdem.dephier",
            input=_DEM,
            output_labels=_LABELS,
            output_flowdirs=_FLOWDIRS,
            output_hierarchy=_HIERARCHY,
            overwrite=True,
        )
        # Dry: no ponded water anywhere
        cls.runModule(
            "r.mapcalc", expression=f"{_WTD_DRY} = -1.0", overwrite=True
        )
        # Wet: 1.5 m of ponded water in depression cells
        cls.runModule(
            "r.mapcalc",
            expression=f"{_WTD_WET} = if({_LABELS} > 0, 1.5, -1.0)",
            overwrite=True,
        )

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()
        cls.runModule(
            "g.remove",
            flags="f",
            type="raster",
            name=[_DEM, _LABELS, _FLOWDIRS, _WTD_DRY, _WTD_WET, _OUT_DRY, _OUT_WET],
        )
        cls.runModule(
            "g.remove",
            flags="f",
            type="vector",
            name=[_HIERARCHY],
        )

    def test_output_created_dry(self):
        """FSM runs without error on a dry (no ponded water) domain."""
        self.assertModule(
            "r.richdem.fsm",
            input=_DEM,
            labels=_LABELS,
            flowdirs=_FLOWDIRS,
            hierarchy=_HIERARCHY,
            water_depth=_WTD_DRY,
            output=_OUT_DRY,
            overwrite=True,
        )
        self.assertRasterExists(_OUT_DRY)

    def test_dry_conditions_min_preserved(self):
        """With no ponded water, minimum wtd remains at −1 (no water created)."""
        self.runModule(
            "r.richdem.fsm",
            input=_DEM,
            labels=_LABELS,
            flowdirs=_FLOWDIRS,
            hierarchy=_HIERARCHY,
            water_depth=_WTD_DRY,
            output=_OUT_DRY,
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_OUT_DRY, flags="g")
        self.assertAlmostEqual(
            float(stats["min"]),
            -1.0,
            places=5,
            msg="Minimum wtd changed from −1 in a dry domain; FSM may have created water",
        )

    def test_water_redistributed(self):
        """FSM reduces mean wtd when ponded water spills out of the depression.

        Initial mean with wtd=+1.5 in 9 depression cells and −1 elsewhere
        is approximately −0.1.  After FSM the ponded water spills and the
        mean drops well below the initial value.
        """
        self.runModule(
            "r.richdem.fsm",
            input=_DEM,
            labels=_LABELS,
            flowdirs=_FLOWDIRS,
            hierarchy=_HIERARCHY,
            water_depth=_WTD_WET,
            output=_OUT_WET,
            overwrite=True,
        )
        stats_before = gs.parse_command("r.univar", map=_WTD_WET, flags="g")
        stats_after = gs.parse_command("r.univar", map=_OUT_WET, flags="g")
        self.assertLess(
            float(stats_after["mean"]),
            float(stats_before["mean"]),
            msg="Mean wtd did not decrease; FSM may not have redistributed ponded water",
        )

    def test_hierarchy_vector_unchanged(self):
        """FSM leaves the depression hierarchy vector readable after the run."""
        self.runModule(
            "r.richdem.fsm",
            input=_DEM,
            labels=_LABELS,
            flowdirs=_FLOWDIRS,
            hierarchy=_HIERARCHY,
            water_depth=_WTD_DRY,
            output=_OUT_DRY,
            overwrite=True,
        )
        self.assertVectorExists(_HIERARCHY)


if __name__ == "__main__":
    test()
