"""Unit tests for solar spectrum and Earth-Sun distance functions.

Tests sixs_E0() and sixs_earth_sun_dist2() from libsixsv.so via the
ctypes wrappers in _support.py.

Run with::

    make test-fortran
    # or directly:
    LIB_SIXSV=./libsixsv.so python3 -m pytest test_solar.py -v
"""

import math
import os
import sys
import unittest

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _support import earth_sun_dist2, solar_E0


class TestSolarSpectrum(unittest.TestCase):

    def test_e0_visible_positive(self):
        """E0 must be positive at every 50 nm step across the VIS/NIR range."""
        wl = np.arange(0.40, 0.91, 0.05, dtype=np.float32)
        E0 = solar_E0(wl)
        for w, e in zip(wl, E0):
            self.assertGreater(float(e), 0.0, msg=f"E0 ≤ 0 at {w:.2f} µm")

    def test_e0_swir_positive(self):
        """E0 must be positive in the SWIR range (1.0–2.5 µm)."""
        wl = np.arange(1.0, 2.51, 0.25, dtype=np.float32)
        E0 = solar_E0(wl)
        self.assertTrue(np.all(E0 > 0), msg=f"Non-positive E0 in SWIR: {E0}")

    def test_e0_reference_visible(self):
        """E0 at key VIS wavelengths must be within 15% of Thuillier reference."""
        references = {0.45: 1980.0, 0.55: 1900.0, 0.65: 1630.0, 0.87: 950.0}
        for wl_um, ref in references.items():
            E0 = solar_E0(float(wl_um))
            self.assertAlmostEqual(
                E0, ref, delta=ref * 0.15,
                msg=f"E0({wl_um} µm) = {E0:.1f}, expected ~{ref:.0f}",
            )

    def test_e0_scalar_returns_float(self):
        E0 = solar_E0(0.55)
        self.assertIsInstance(E0, float)
        self.assertGreater(E0, 0.0)

    def test_e0_array_returns_array(self):
        wl = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32)
        E0 = solar_E0(wl)
        self.assertEqual(len(E0), len(wl))
        self.assertTrue(np.all(np.isfinite(E0)))

    def test_e0_blue_greater_than_swir(self):
        """Broad spectral trend: E0 at 0.45 µm must exceed E0 at 2.0 µm."""
        self.assertGreater(solar_E0(0.45), solar_E0(2.0))

    def test_e0_all_finite(self):
        """No NaN or Inf in E0 across 0.25–4.0 µm."""
        wl = np.arange(0.25, 4.01, 0.05, dtype=np.float32)
        E0 = solar_E0(wl)
        self.assertTrue(
            np.all(np.isfinite(E0)),
            msg=f"Non-finite E0 at: {wl[~np.isfinite(E0)]}",
        )


class TestEarthSunDist(unittest.TestCase):

    def test_perihelion_less_than_one(self):
        """Near perihelion (DOY 3) Earth is closest: d² must be < 1."""
        d2 = earth_sun_dist2(3)
        self.assertLess(d2, 1.0, msg=f"d²(DOY=3) = {d2:.6f}, expected < 1.0")

    def test_aphelion_greater_than_one(self):
        """Near aphelion (DOY 185) Earth is farthest: d² must be > 1."""
        d2 = earth_sun_dist2(185)
        self.assertGreater(d2, 1.0, msg=f"d²(DOY=185) = {d2:.6f}, expected > 1.0")

    def test_all_days_positive_finite(self):
        """d² must be positive and finite for every calendar day."""
        for doy in range(1, 366):
            d2 = earth_sun_dist2(doy)
            self.assertGreater(d2, 0.0, msg=f"d² ≤ 0 at DOY {doy}")
            self.assertTrue(math.isfinite(d2), msg=f"d² non-finite at DOY {doy}")

    def test_annual_variation_within_4pct(self):
        """d² must stay within 4% of 1 AU² all year (Earth eccentricity ~0.0167)."""
        for doy in range(1, 366):
            d2 = earth_sun_dist2(doy)
            self.assertAlmostEqual(
                d2, 1.0, delta=0.04,
                msg=f"d²(DOY={doy}) = {d2:.4f} outside ±4% of 1 AU²",
            )

    def test_eccentricity_range(self):
        """Peak-to-peak variation in d² must be ~6.7% (≈ 4e, e=0.0167)."""
        d2_all = [earth_sun_dist2(d) for d in range(1, 366)]
        rng = max(d2_all) - min(d2_all)
        self.assertGreater(rng, 0.055, msg=f"Annual d² range {rng:.4f} < 5.5%")
        self.assertLess(rng, 0.080, msg=f"Annual d² range {rng:.4f} > 8.0%")

    def test_symmetry_perihelion_aphelion(self):
        """d²(perihelion) + d²(aphelion) ≈ 2 (symmetric about 1 AU²)."""
        d2_all  = [earth_sun_dist2(d) for d in range(1, 366)]
        d2_min  = min(d2_all)
        d2_max  = max(d2_all)
        self.assertAlmostEqual(
            d2_min + d2_max, 2.0, delta=0.01,
            msg=f"d²_min + d²_max = {d2_min + d2_max:.4f}, expected ≈ 2.0",
        )


if __name__ == "__main__":
    unittest.main()
