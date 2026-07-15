"""Unit tests for solar spectrum and Earth-Sun distance functions.

Tests sixs_E0() and sixs_earth_sun_dist2() from libatcorr.so via the
Python ctypes bindings in python/atcorr.py.

Run from a GRASS session:
    python -m grass.gunittest.main
"""

import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import atcorr as ac

from grass.gunittest.case import TestCase
from grass.gunittest.main import test


class TestSolarSpectrum(TestCase):
    """Tests for solar_E0(): Thuillier solar irradiance spectrum."""

    def test_e0_visible_positive(self):
        """E0 must be positive at every 50 nm step across the VIS/NIR range."""
        wl = np.arange(0.40, 0.91, 0.05, dtype=np.float32)
        E0 = ac.solar_E0(wl)
        for w, e in zip(wl, E0):
            self.assertGreater(float(e), 0.0, msg=f"E0 ≤ 0 at {w:.2f} µm")

    def test_e0_swir_positive(self):
        """E0 must be positive in the SWIR range (1.0–2.5 µm)."""
        wl = np.arange(1.0, 2.51, 0.25, dtype=np.float32)
        E0 = ac.solar_E0(wl)
        self.assertTrue(np.all(E0 > 0), msg=f"Non-positive E0 in SWIR: {E0}")

    def test_e0_reference_visible(self):
        """E0 at key VIS wavelengths must be within 15% of Thuillier reference."""
        # Approximate published values (W m⁻² µm⁻¹)
        references = {0.45: 1980.0, 0.55: 1900.0, 0.65: 1630.0, 0.87: 950.0}
        for wl_um, ref in references.items():
            E0 = ac.solar_E0(float(wl_um))
            self.assertAlmostEqual(
                E0, ref, delta=ref * 0.15,
                msg=f"E0({wl_um} µm) = {E0:.1f}, expected ~{ref:.0f}",
            )

    def test_e0_scalar_returns_float(self):
        """Scalar wavelength input must return a Python float."""
        E0 = ac.solar_E0(0.55)
        self.assertIsInstance(E0, float)
        self.assertGreater(E0, 0.0)

    def test_e0_array_returns_array(self):
        """Array input must return an array of matching length."""
        wl = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32)
        E0 = ac.solar_E0(wl)
        self.assertEqual(len(E0), len(wl))
        self.assertTrue(np.all(np.isfinite(E0)))

    def test_e0_blue_greater_than_swir(self):
        """Broad spectral trend: E0 at 0.45 µm must exceed E0 at 2.0 µm."""
        self.assertGreater(ac.solar_E0(0.45), ac.solar_E0(2.0))

    def test_e0_all_finite(self):
        """No NaN or Inf in E0 across 0.25–4.0 µm."""
        wl = np.arange(0.25, 4.01, 0.05, dtype=np.float32)
        E0 = ac.solar_E0(wl)
        self.assertTrue(
            np.all(np.isfinite(E0)),
            msg=f"Non-finite E0 at: {wl[~np.isfinite(E0)]}",
        )

    def test_e0_peak_in_visible(self):
        """Peak solar irradiance must occur in the 0.45–0.60 µm visible range."""
        wl  = np.arange(0.25, 2.51, 0.005, dtype=np.float32)
        E0  = ac.solar_E0(wl)
        peak_wl = float(wl[np.argmax(E0)])
        self.assertGreater(peak_wl, 0.40, msg=f"Peak E0 at {peak_wl:.3f} µm < 0.40")
        self.assertLess(peak_wl,    0.65, msg=f"Peak E0 at {peak_wl:.3f} µm > 0.65")

    def test_e0_integral_vis_nir(self):
        """Integral of E0 over 0.35–2.5 µm must be in [700, 1200] W/m².

        The total solar constant is ~1361 W/m²; integrating only the
        0.35–2.5 µm window captures roughly 70–90% of it.
        """
        wl  = np.arange(0.35, 2.505, 0.005, dtype=np.float32)
        E0  = ac.solar_E0(wl)
        integral = float(np.trapezoid(E0, wl))   # trapezoidal rule
        self.assertGreater(integral, 700.0,
                           msg=f"E0 integral over 0.35–2.5 µm = {integral:.0f} W/m² < 700")
        self.assertLess(integral, 1400.0,
                        msg=f"E0 integral over 0.35–2.5 µm = {integral:.0f} W/m² > 1400")


class TestEarthSunDist(TestCase):
    """Tests for earth_sun_dist2(): seasonal Earth-Sun distance squared."""

    def test_perihelion_less_than_one(self):
        """Near perihelion (DOY 3) Earth is closest: d² must be < 1."""
        d2 = ac.earth_sun_dist2(3)
        self.assertLess(
            d2, 1.0, msg=f"d²(DOY=3) = {d2:.6f}, expected < 1.0"
        )

    def test_aphelion_greater_than_one(self):
        """Near aphelion (DOY 185) Earth is farthest: d² must be > 1."""
        d2 = ac.earth_sun_dist2(185)
        self.assertGreater(
            d2, 1.0, msg=f"d²(DOY=185) = {d2:.6f}, expected > 1.0"
        )

    def test_all_days_positive_finite(self):
        """d² must be positive and finite for every calendar day."""
        for doy in range(1, 366):
            d2 = ac.earth_sun_dist2(doy)
            self.assertGreater(d2, 0.0, msg=f"d² ≤ 0 at DOY {doy}")
            self.assertTrue(math.isfinite(d2), msg=f"d² non-finite at DOY {doy}")

    def test_annual_variation_within_4pct(self):
        """d² must stay within 4% of 1 AU² all year (Earth eccentricity ~0.0167)."""
        for doy in range(1, 366):
            d2 = ac.earth_sun_dist2(doy)
            self.assertAlmostEqual(
                d2, 1.0, delta=0.04,
                msg=f"d²(DOY={doy}) = {d2:.4f} outside ±4% of 1 AU²",
            )

    def test_eccentricity_range(self):
        """Peak-to-peak variation in d² must be ~6.7% (orbital eccentricity 0.0167).

        earth_sun_dist2 returns d² (AU²).  For e=0.0167:
          d²_max - d²_min = (1+e)² - (1-e)² = 4e ≈ 0.0668
        (not 3.3% which is the variation in d, not d²).
        """
        d2_all = [ac.earth_sun_dist2(d) for d in range(1, 366)]
        rng = max(d2_all) - min(d2_all)
        self.assertGreater(rng, 0.055, msg=f"Annual d² range {rng:.4f} < 5.5%")
        self.assertLess(rng, 0.080, msg=f"Annual d² range {rng:.4f} > 8.0%")

    def test_symmetry_perihelion_aphelion(self):
        """d²(perihelion) + d²(aphelion) ≈ 2 (symmetric about 1 AU²)."""
        d2_min = min(ac.earth_sun_dist2(d) for d in range(1, 366))
        d2_max = max(ac.earth_sun_dist2(d) for d in range(1, 366))
        self.assertAlmostEqual(
            d2_min + d2_max, 2.0, delta=0.01,
            msg=f"d²_min + d²_max = {d2_min + d2_max:.4f}, expected ≈ 2.0",
        )


if __name__ == "__main__":
    test()
