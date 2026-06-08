#!/usr/bin/env python3

"""
Tests for r.cell.area

Coverage
--------
- Projected CRS (UTM, metres): m² and km² values, overwrite protection
- Geographic CRS (degrees): m² and km² via spherical formula
- Projected CRS (US survey feet): m² and km² via meters conversion factor
- XY (unprojected) location: module must exit non-zero
"""

import math
import subprocess

import grass.script as gs
from grass.gunittest.case import TestCase
from grass.gunittest.main import test


OUTPUT = "test_r_cell_area"


def _grass_tmp_flag():
    """Return the GRASS flag for creating a temporary project.

    GRASS 8.4+ uses ``--tmp-project``; older releases use ``--tmp-location``.
    The result is cached after the first call.
    """
    if not hasattr(_grass_tmp_flag, "_cached"):
        result = subprocess.run(["grass", "--help"], capture_output=True, text=True)
        combined = result.stdout + result.stderr
        _grass_tmp_flag._cached = (
            "--tmp-project" if "--tmp-project" in combined else "--tmp-location"
        )
    return _grass_tmp_flag._cached


def _run_in_tmp_project(proj_arg, bash_commands, timeout=120):
    """Run one or more GRASS commands in a temporary project.

    *proj_arg* is passed directly to ``grass --tmp-project`` (or the
    older ``--tmp-location`` on GRASS < 8.4), e.g. ``"XY"`` or
    ``"EPSG:4326"``.  *bash_commands* is a single shell string executed
    via ``bash -c``.

    Returns ``(returncode, stdout, stderr)``.
    """
    result = subprocess.run(
        ["grass", _grass_tmp_flag(), proj_arg, "--exec", "bash", "-c", bash_commands],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return result.returncode, result.stdout, result.stderr


def _parse_univar(text):
    """Parse ``r.univar -g`` key=value output into a dict of floats."""
    out = {}
    for line in text.splitlines():
        line = line.strip()
        if "=" in line:
            k, _, v = line.partition("=")
            try:
                out[k.strip()] = float(v.strip())
            except ValueError:
                pass
    return out


class TestRCellAreaMeters(TestCase):
    """Projected CRS (UTM metres) — runs inside the NC sample dataset."""

    @classmethod
    def setUpClass(cls):
        cls.use_temp_region()
        # Small region with an exact 10 m resolution
        cls.runModule("g.region", n=228500, s=228000, e=637000, w=636500, res=10)

    @classmethod
    def tearDownClass(cls):
        cls.del_temp_region()

    def tearDown(self):
        self.runModule("g.remove", flags="f", type="raster", name=OUTPUT, quiet=True)

    def test_m2_with_10m_cells(self):
        """10 m × 10 m cells in UTM → every cell = 100.0 m²."""
        self.assertModule("r.cell.area", output=OUTPUT, units="m2")
        self.assertRasterFitsUnivar(
            raster=OUTPUT,
            reference="min=100\nmax=100",
            precision=1e-6,
        )

    def test_km2_with_1000m_cells(self):
        """1000 m × 1000 m cells in UTM → every cell = 1.0 km²."""
        self.runModule("g.region", res=1000)
        self.assertModule("r.cell.area", output=OUTPUT, units="km2")
        self.assertRasterFitsUnivar(
            raster=OUTPUT,
            reference="min=1\nmax=1",
            precision=1e-9,
        )

    def test_overwrite_protection(self):
        """Running without the overwrite flag when the output already exists must fail."""
        self.runModule("r.cell.area", output=OUTPUT, units="m2")
        self.assertModuleFail("r.cell.area", output=OUTPUT, units="m2")

    def test_overwrite_flag(self):
        """Running with overwrite=True when the output already exists must succeed."""
        self.runModule("r.cell.area", output=OUTPUT, units="m2")
        self.assertModule("r.cell.area", output=OUTPUT, units="m2", overwrite=True)
        self.assertRasterExists(OUTPUT)


class TestRCellAreaDegrees(TestCase):
    """Geographic CRS (EPSG:4326) — spawns a temporary GRASS project."""

    # 1°×1° cell centred at lat=0.5° (equator region)
    # Expected values computed from the spherical formula in r.cell.area:
    #   m2  = (111195 * nsres) * (ewres * pi/180 * 6371000 * cos(lat_centre))
    #   km2 = (111.195 * nsres) * (ewres * pi/180 * 6371    * cos(lat_centre))
    _lat_centre = 0.5  # degrees
    _expected_m2 = (111195.0 * 1.0) * (
        1.0 * (math.pi / 180.0) * 6371000.0 * math.cos(_lat_centre * math.pi / 180.0)
    )
    _expected_km2 = _expected_m2 / 1.0e6
    # Allow 0.01 % relative tolerance (rounding in mapcalc float arithmetic)
    _rel_tol = 1e-4

    def _run_and_parse(self, units):
        """Run r.cell.area in EPSG:4326 at res=1 and return univar stats."""
        rc, stdout, stderr = _run_in_tmp_project(
            "EPSG:4326",
            (
                "g.region n=1 s=0 e=1 w=0 res=1 && "
                f"r.cell.area output=area units={units} && "
                "r.univar map=area flags=g separator='='"
            ),
        )
        self.assertEqual(
            rc,
            0,
            msg=f"r.cell.area in EPSG:4326 failed (units={units}):\n{stderr}",
        )
        return _parse_univar(stdout)

    def test_m2_spherical_formula(self):
        """Geographic CRS m² matches the spherical approximation."""
        stats = self._run_and_parse("m2")
        self.assertIn("min", stats)
        self.assertIn("max", stats)
        # Single cell → min == max
        self.assertAlmostEqual(
            stats["min"],
            stats["max"],
            delta=1.0,
            msg="min and max should be equal for a single-cell region",
        )
        self.assertAlmostEqual(
            stats["min"],
            self._expected_m2,
            delta=self._expected_m2 * self._rel_tol,
            msg=(
                f"m² value {stats['min']:.0f} differs from expected "
                f"{self._expected_m2:.0f} by more than {self._rel_tol * 100}%"
            ),
        )

    def test_km2_consistent_with_m2(self):
        """Geographic CRS km² output equals m² / 1 000 000."""
        stats_m2 = self._run_and_parse("m2")
        stats_km2 = self._run_and_parse("km2")
        ratio = stats_m2["min"] / stats_km2["min"]
        self.assertAlmostEqual(
            ratio,
            1.0e6,
            delta=1.0e6 * self._rel_tol,
            msg=f"km² / m² ratio {ratio:.2f} differs from 1 000 000",
        )


class TestRCellAreaFeet(TestCase):
    """Projected CRS in US survey feet (EPSG:2249) — spawns a temporary GRASS project.

    EPSG:2249 is NAD83 / Massachusetts Mainland (US survey feet).
    The PROJ conversion factor is 0.304800609601219 m per US survey foot,
    so a 100 ft × 100 ft cell has an area of
    100 * 100 * (0.304800609601219)² ≈ 929.034 m².
    """

    _m_per_usft = 0.304800609601219
    _cell_ft = 100.0
    _expected_m2 = _cell_ft**2 * _m_per_usft**2  # ≈ 929.034116 m²
    _expected_km2 = _expected_m2 / 1.0e6
    _rel_tol = 1e-4

    def _run_and_parse(self, units):
        """Run r.cell.area in EPSG:2249 with 100 ft cells and return univar stats."""
        rc, stdout, stderr = _run_in_tmp_project(
            "EPSG:2249",
            (
                "g.region n=100 s=0 e=100 w=0 res=100 && "
                f"r.cell.area output=area units={units} && "
                "r.univar map=area flags=g separator='='"
            ),
        )
        self.assertEqual(
            rc,
            0,
            msg=f"r.cell.area in EPSG:2249 failed (units={units}):\n{stderr}",
        )
        return _parse_univar(stdout)

    def test_m2_in_us_survey_feet_crs(self):
        """US survey feet CRS: 100 ft × 100 ft cell ≈ 929.034 m²."""
        stats = self._run_and_parse("m2")
        self.assertIn("min", stats)
        self.assertAlmostEqual(
            stats["min"],
            self._expected_m2,
            delta=self._expected_m2 * self._rel_tol,
            msg=(
                f"m² value {stats['min']:.6f} differs from expected "
                f"{self._expected_m2:.6f} by more than {self._rel_tol * 100}%"
            ),
        )

    def test_km2_in_us_survey_feet_crs(self):
        """US survey feet CRS: 100 ft × 100 ft cell ≈ 9.29034e-4 km²."""
        stats = self._run_and_parse("km2")
        self.assertIn("min", stats)
        self.assertAlmostEqual(
            stats["min"],
            self._expected_km2,
            delta=self._expected_km2 * self._rel_tol,
            msg=(
                f"km² value {stats['min']:.9f} differs from expected "
                f"{self._expected_km2:.9f} by more than {self._rel_tol * 100}%"
            ),
        )


class TestRCellAreaXY(TestCase):
    """XY (unprojected) location must produce a non-zero exit code."""

    def test_xy_location_raises_fatal(self):
        """r.cell.area must fail with a fatal error in an XY location."""
        rc, _stdout, _stderr = _run_in_tmp_project(
            "XY",
            "r.cell.area output=area units=m2",
        )
        self.assertNotEqual(
            rc,
            0,
            msg="r.cell.area should exit non-zero in an XY (unprojected) location",
        )


if __name__ == "__main__":
    test()
