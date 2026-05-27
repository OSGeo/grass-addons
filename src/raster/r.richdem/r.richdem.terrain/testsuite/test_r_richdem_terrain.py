"""Tests for r.richdem.terrain

Synthetic DEM (5 x 5, 1 m resolution) — uniform south-facing slope:

    5 5 5 5 5   (row 1, north)
    4 4 4 4 4
    3 3 3 3 3
    2 2 2 2 2
    1 1 1 1 1   (row 5, south)

Grid spacing is 1 m in both directions.  Expected terrain attribute values
for this planar surface:

  - slope_degrees: interior N-S cells have exactly 45° (arctan(1 m / 1 m));
    diagonal corner cells produce lower values (~22°).  Max = 45°.
  - slope_radians: max = π/4 ≈ 0.785.
  - aspect: mean = 180° (south-facing).
  - curvature: mean = 0 (planar surface has no net curvature).
"""

import math
import unittest

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test

try:
    import _richdem  # noqa: F401

    HAS_RICHDEM = True
except ImportError:
    HAS_RICHDEM = False

_DEM = "tmp_richdem_terrain_dem"
_OUT = "tmp_richdem_terrain_out"

# Uniform south-facing slope: row 1 (north) = 5, row 5 (south) = 1
_DEM_EXPR = "6 - row()"

_ALL_ATTRIBUTES = [
    "slope_riserun",
    "slope_percentage",
    "slope_degrees",
    "slope_radians",
    "aspect",
    "curvature",
    "planform_curvature",
    "profile_curvature",
]


@unittest.skipUnless(
    HAS_RICHDEM,
    "RichDEM _richdem extension not found; "
    "set PYTHONPATH to richdem/wrappers/pyrichdem",
)
class TestRichdemTerrain(TestCase):
    """Functional tests for r.richdem.terrain requiring the RichDEM extension."""

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
            "g.remove", flags="f", type="raster", name=[_DEM, _OUT]
        )

    def test_all_attributes_produce_output(self):
        """Every supported attribute option produces an output raster."""
        for attr in _ALL_ATTRIBUTES:
            with self.subTest(attribute=attr):
                self.assertModule(
                    "r.richdem.terrain",
                    input=_DEM,
                    output=_OUT,
                    attribute=attr,
                    overwrite=True,
                )
                self.assertRasterExists(_OUT)

    def test_slope_degrees_max_is_45(self):
        """Interior N-S cells on a 1:1 slope have slope = arctan(1) = 45°."""
        self.runModule(
            "r.richdem.terrain",
            input=_DEM,
            output=_OUT,
            attribute="slope_degrees",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_OUT, flags="g")
        self.assertAlmostEqual(
            float(stats["max"]),
            45.0,
            places=3,
            msg="Maximum slope_degrees on a 1:1 slope should be 45°",
        )

    def test_slope_radians_max_is_pi_over_4(self):
        """Interior N-S cells on a 1:1 slope have slope = π/4 radians."""
        self.runModule(
            "r.richdem.terrain",
            input=_DEM,
            output=_OUT,
            attribute="slope_radians",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_OUT, flags="g")
        self.assertAlmostEqual(
            float(stats["max"]),
            math.pi / 4,
            places=3,
            msg="Maximum slope_radians on a 1:1 slope should be π/4",
        )

    def test_aspect_mean_south(self):
        """Mean aspect of a uniform south-facing slope is 180°."""
        self.runModule(
            "r.richdem.terrain",
            input=_DEM,
            output=_OUT,
            attribute="aspect",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_OUT, flags="g")
        self.assertAlmostEqual(
            float(stats["mean"]),
            180.0,
            places=3,
            msg="Mean aspect of a south-facing slope should be 180°",
        )

    def test_curvature_mean_zero(self):
        """Mean curvature of a planar surface is 0."""
        self.runModule(
            "r.richdem.terrain",
            input=_DEM,
            output=_OUT,
            attribute="curvature",
            overwrite=True,
        )
        stats = gs.parse_command("r.univar", map=_OUT, flags="g")
        self.assertAlmostEqual(
            float(stats["mean"]),
            0.0,
            places=3,
            msg="Mean curvature of a planar slope should be 0",
        )


if __name__ == "__main__":
    test()
