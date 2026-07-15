"""Unit tests for LUT computation, slicing, and reflectance inversion.

Tests compute_lut(), lut_slice(), and invert() from libatcorr.so via the
Python ctypes bindings in python/atcorr.py.

Run from a GRASS session:
    python -m grass.gunittest.main
"""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "python"))
import atcorr as ac

from grass.gunittest.case import TestCase
from grass.gunittest.main import test

# ── Shared small LUT grid used by most tests ──────────────────────────────────
_WL  = np.array([0.45, 0.55, 0.65, 0.87], dtype=np.float32)  # 4 bands
_AOD = np.array([0.0, 0.2, 0.6],          dtype=np.float32)  # 3 AOD points
_H2O = np.array([1.0, 3.0],               dtype=np.float32)  # 2 H2O points

_BASE_CFG = dict(
    wl=_WL, aod=_AOD, h2o=_H2O,
    sza=35.0, vza=5.0, raa=90.0,
    altitude_km=1000.0,
    atmo_model=1,     # US Standard 1962
    aerosol_model=1,  # continental
    ozone_du=300.0,
)


def _make_lut(**kwargs):
    """Helper: build LutConfig and compute LUT, merging kwargs over _BASE_CFG."""
    cfg = ac.LutConfig(**{**_BASE_CFG, **kwargs})
    return cfg, ac.compute_lut(cfg)


class TestLutShape(TestCase):
    """Tests for output array shapes from compute_lut()."""

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_shape(self):
        expected = (len(_AOD), len(_H2O), len(_WL))
        self.assertEqual(self.lut.R_atm.shape, expected)

    def test_T_down_shape(self):
        expected = (len(_AOD), len(_H2O), len(_WL))
        self.assertEqual(self.lut.T_down.shape, expected)

    def test_T_up_shape(self):
        expected = (len(_AOD), len(_H2O), len(_WL))
        self.assertEqual(self.lut.T_up.shape, expected)

    def test_s_alb_shape(self):
        expected = (len(_AOD), len(_H2O), len(_WL))
        self.assertEqual(self.lut.s_alb.shape, expected)


class TestLutPhysicalBounds(TestCase):
    """Tests that all LUT values satisfy physical constraints."""

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_non_negative(self):
        self.assertTrue(
            np.all(self.lut.R_atm >= 0.0),
            msg=f"Negative R_atm: min = {self.lut.R_atm.min():.4f}",
        )

    def test_R_atm_less_than_one(self):
        self.assertTrue(
            np.all(self.lut.R_atm < 1.0),
            msg=f"R_atm ≥ 1: max = {self.lut.R_atm.max():.4f}",
        )

    def test_T_down_positive(self):
        self.assertTrue(np.all(self.lut.T_down > 0.0))

    def test_T_down_le_one(self):
        self.assertTrue(
            np.all(self.lut.T_down <= 1.0 + 1e-5),
            msg=f"T_down > 1: max = {self.lut.T_down.max():.4f}",
        )

    def test_T_up_positive(self):
        self.assertTrue(np.all(self.lut.T_up > 0.0))

    def test_T_up_le_one(self):
        self.assertTrue(
            np.all(self.lut.T_up <= 1.0 + 1e-5),
            msg=f"T_up > 1: max = {self.lut.T_up.max():.4f}",
        )

    def test_s_alb_non_negative(self):
        self.assertTrue(np.all(self.lut.s_alb >= 0.0))

    def test_s_alb_less_than_one(self):
        self.assertTrue(
            np.all(self.lut.s_alb < 1.0),
            msg=f"s_alb ≥ 1: max = {self.lut.s_alb.max():.4f}",
        )

    def test_all_finite(self):
        for name in ("R_atm", "T_down", "T_up", "s_alb"):
            arr = getattr(self.lut, name)
            self.assertTrue(
                np.all(np.isfinite(arr)),
                msg=f"Non-finite values in {name}",
            )


class TestLutMonotonicity(TestCase):
    """Tests that LUT arrays are monotone with respect to AOD."""

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_R_atm_non_decreasing_with_aod(self):
        """R_atm must be non-decreasing as AOD increases (at each H2O/WL)."""
        for i_h in range(len(_H2O)):
            for i_w, wl in enumerate(_WL):
                r = self.lut.R_atm[:, i_h, i_w]
                for k in range(len(_AOD) - 1):
                    self.assertGreaterEqual(
                        r[k + 1], r[k] - 1e-4,
                        msg=(
                            f"R_atm decreased with AOD at "
                            f"h2o={_H2O[i_h]:.1f} wl={wl:.2f}: "
                            f"{r[k]:.4f} → {r[k+1]:.4f}"
                        ),
                    )

    def test_T_total_non_increasing_with_aod(self):
        """T_down × T_up must be non-increasing as AOD increases."""
        for i_h in range(len(_H2O)):
            for i_w, wl in enumerate(_WL):
                T = (
                    self.lut.T_down[:, i_h, i_w]
                    * self.lut.T_up[:, i_h, i_w]
                )
                for k in range(len(_AOD) - 1):
                    self.assertLessEqual(
                        T[k + 1], T[k] + 1e-4,
                        msg=(
                            f"T_total increased with AOD at "
                            f"h2o={_H2O[i_h]:.1f} wl={wl:.2f}: "
                            f"{T[k]:.4f} → {T[k+1]:.4f}"
                        ),
                    )


class TestLutAerosolModels(TestCase):
    """Tests comparing different aerosol models."""

    def test_rayleigh_only_R_atm_at_blue(self):
        """Rayleigh-only (aerosol=0) R_atm at 450 nm must be in [0.05, 0.20]."""
        _, lut = _make_lut(aerosol_model=0)
        R_blue = float(lut.R_atm[0, 0, 0])  # AOD=0, H2O=1.0, wl=0.45 µm
        self.assertGreater(R_blue, 0.05, msg=f"R_atm(Rayleigh, 450nm) too low: {R_blue:.4f}")
        self.assertLess(R_blue, 0.20, msg=f"R_atm(Rayleigh, 450nm) too high: {R_blue:.4f}")

    def test_continental_maritime_differ(self):
        """Continental and maritime aerosol models must give different R_atm."""
        _, lut_c = _make_lut(aerosol_model=1)
        _, lut_m = _make_lut(aerosol_model=2)
        # At maximum AOD, at some wavelength they must differ
        diff = np.abs(lut_c.R_atm[-1] - lut_m.R_atm[-1]).max()
        self.assertGreater(diff, 1e-4, msg="Continental and maritime R_atm identical")

    def test_no_aerosol_lower_R_atm_at_blue(self):
        """Rayleigh-only R_atm at max AOD must be ≤ continental at 450 nm."""
        _, lut_c = _make_lut(aerosol_model=1)
        _, lut_n = _make_lut(aerosol_model=0)
        self.assertLessEqual(
            float(lut_n.R_atm[-1, 0, 0]),
            float(lut_c.R_atm[-1, 0, 0]) + 1e-4,
        )


class TestLutSlice(TestCase):
    """Tests for lut_slice(): bilinear interpolation at fixed (AOD, H2O)."""

    @classmethod
    def setUpClass(cls):
        cls.cfg, cls.lut = _make_lut()

    def test_slice_shape_is_1d(self):
        """lut_slice output must be 1-D arrays of length n_wl."""
        sl = ac.lut_slice(self.cfg, self.lut, float(_AOD[1]), float(_H2O[0]))
        for name in ("R_atm", "T_down", "T_up", "s_alb"):
            arr = getattr(sl, name)
            self.assertEqual(
                len(arr), len(_WL),
                msg=f"Slice {name} shape {arr.shape} ≠ ({len(_WL)},)",
            )

    def test_slice_at_first_grid_node_matches_lut(self):
        """Slice at exact grid node (aod[0], h2o[0]) must match LUT row."""
        sl = ac.lut_slice(self.cfg, self.lut, float(_AOD[0]), float(_H2O[0]))
        np.testing.assert_allclose(
            sl.R_atm, self.lut.R_atm[0, 0, :], atol=1e-4,
            err_msg="lut_slice at grid node differs from LUT array",
        )

    def test_slice_at_last_grid_node_matches_lut(self):
        """Slice at exact grid node (aod[-1], h2o[-1]) must match LUT row."""
        sl = ac.lut_slice(self.cfg, self.lut, float(_AOD[-1]), float(_H2O[-1]))
        np.testing.assert_allclose(
            sl.R_atm, self.lut.R_atm[-1, -1, :], atol=1e-4,
        )

    def test_slice_between_nodes_physical(self):
        """Interpolated values at midpoint must obey physical bounds."""
        aod_mid = float((_AOD[0] + _AOD[1]) / 2)
        h2o_mid = float((_H2O[0] + _H2O[1]) / 2)
        sl = ac.lut_slice(self.cfg, self.lut, aod_mid, h2o_mid)
        self.assertTrue(np.all(sl.R_atm >= 0.0))
        self.assertTrue(np.all(sl.R_atm < 1.0))
        self.assertTrue(np.all(sl.T_down > 0.0))
        self.assertTrue(np.all(sl.s_alb >= 0.0))

    def test_slice_R_atm_increases_with_aod(self):
        """R_atm from sequential slices must be non-decreasing with AOD."""
        r_vals = [
            float(ac.lut_slice(self.cfg, self.lut, float(a), float(_H2O[0])).R_atm[0])
            for a in _AOD
        ]
        for k in range(len(r_vals) - 1):
            self.assertGreaterEqual(
                r_vals[k + 1], r_vals[k] - 1e-4,
                msg=f"R_atm decreased: {r_vals[k]:.4f} → {r_vals[k+1]:.4f}",
            )


class TestInversion(TestCase):
    """Tests for invert(): algebraic TOA → BOA reflectance inversion."""

    def test_no_atmosphere_identity(self):
        """With R_atm=0, T=1, s_alb=0: rho_boa must equal rho_toa."""
        rho_toa = np.array([0.1, 0.2, 0.3, 0.5], dtype=np.float32)
        rho_boa = ac.invert(rho_toa, 0.0, 1.0, 1.0, 0.0)
        np.testing.assert_allclose(rho_boa, rho_toa, atol=1e-5)

    def test_atmosphere_reduces_bright_surface(self):
        """Atmosphere with high T removes path radiance: rho_boa < rho_toa.

        Parameters chosen so T_down*T_up ≈ 0.95 >> R_atm/rho_toa, which
        ensures the atmospheric correction lowers the apparent reflectance.
        """
        rho_boa = ac.invert(0.5, 0.10, 0.98, 0.98, 0.05)
        self.assertLess(float(rho_boa), 0.5)

    def test_bright_surface_stays_bright(self):
        """Very bright TOA (≈0.8) corrected must still give rho_boa > 0.5."""
        rho_boa = ac.invert(0.80, 0.08, 0.85, 0.90, 0.05)
        self.assertGreater(float(rho_boa), 0.5)

    def test_dark_surface_stays_dark(self):
        """Dark TOA (≈0.05) corrected must give rho_boa < 0.15."""
        rho_boa = ac.invert(0.05, 0.03, 0.92, 0.95, 0.02)
        self.assertLess(float(rho_boa), 0.15)

    def test_full_pipeline_physical_range(self):
        """Full pipeline: compute LUT → slice → invert; rho_boa must be in [-0.05, 1]."""
        cfg, lut = _make_lut()
        sl = ac.lut_slice(cfg, lut, 0.2, 2.0)
        # Moderate TOA reflectance, realistic for land surface
        rho_toa = np.array([0.12, 0.10, 0.09, 0.08], dtype=np.float32)
        rho_boa = ac.invert(rho_toa, sl.R_atm, sl.T_down, sl.T_up, sl.s_alb)
        self.assertTrue(np.all(np.isfinite(rho_boa)))
        self.assertTrue(np.all(rho_boa >= -0.05))
        self.assertTrue(np.all(rho_boa < 1.0))

    def test_vectorised_over_pixels(self):
        """invert() must work element-wise for an array of 100 pixels."""
        rho_toa = np.random.uniform(0.05, 0.50, 100).astype(np.float32)
        rho_boa = ac.invert(rho_toa, 0.05, 0.90, 0.92, 0.08)
        self.assertEqual(len(rho_boa), 100)
        self.assertTrue(np.all(np.isfinite(rho_boa)))

    def test_forward_inverse_roundtrip(self):
        """Forward model → invert must recover the original rho_boa within 1e-4."""
        cfg, lut = _make_lut()
        sl = ac.lut_slice(cfg, lut, 0.15, 2.0)
        rho_boa_orig = np.array([0.04, 0.08, 0.15, 0.25], dtype=np.float32)  # n_wl=4
        # Lambertian forward model: ρ_toa = R_atm + T_dn·T_up·ρ_boa / (1 - s·ρ_boa)
        rho_toa = (sl.R_atm
                   + sl.T_down * sl.T_up * rho_boa_orig
                   / (1.0 - sl.s_alb * rho_boa_orig))
        rho_boa_rec = ac.invert(rho_toa, sl.R_atm, sl.T_down, sl.T_up, sl.s_alb)
        np.testing.assert_allclose(
            rho_boa_rec, rho_boa_orig, rtol=1e-4, atol=1e-5,
            err_msg="Roundtrip forward→invert failed",
        )


class TestLutSpectralBehavior(TestCase):
    """Tests for physically expected spectral structure of LUT arrays."""

    @classmethod
    def setUpClass(cls):
        cls.cfg_ray, cls.lut_ray = _make_lut(aerosol_model=0)   # Rayleigh only
        cls.cfg_co,  cls.lut_co  = _make_lut(aerosol_model=1)   # continental

    def test_R_atm_blue_greater_than_nir_rayleigh(self):
        """Rayleigh-only R_atm at 450 nm must be >> R_atm at 870 nm (τ ∝ λ⁻⁴)."""
        R_blue = float(self.lut_ray.R_atm[0, 0, 0])   # AOD=0, H2O=1.0, 450 nm
        R_nir  = float(self.lut_ray.R_atm[0, 0, -1])  # 870 nm
        self.assertGreater(
            R_blue, R_nir * 3.0,
            msg=f"R_atm(Rayleigh): 450nm={R_blue:.4f}, 870nm={R_nir:.4f} — expected ratio >3",
        )

    def test_T_total_blue_less_than_nir_rayleigh(self):
        """Rayleigh extinction: T_down×T_up at 450 nm must be less than at 870 nm."""
        T_blue = float(self.lut_ray.T_down[0, 0, 0] * self.lut_ray.T_up[0, 0, 0])
        T_nir  = float(self.lut_ray.T_down[0, 0, -1] * self.lut_ray.T_up[0, 0, -1])
        self.assertLess(
            T_blue, T_nir,
            msg=f"T_total(Rayleigh): 450nm={T_blue:.4f} ≥ 870nm={T_nir:.4f}",
        )

    def test_aerosol_increases_R_atm_red(self):
        """Continental aerosol at max AOD must raise R_atm at 650 nm vs Rayleigh-only."""
        R_ray = float(self.lut_ray.R_atm[-1, 0, 2])  # 650 nm, max AOD
        R_co  = float(self.lut_co.R_atm[-1, 0, 2])
        self.assertGreater(
            R_co, R_ray,
            msg=f"R_atm(650nm): continental={R_co:.4f} ≤ Rayleigh-only={R_ray:.4f}",
        )

    def test_R_atm_spectral_ordering_with_aerosol(self):
        """With continental aerosol at moderate AOD, R_atm(450nm) > R_atm(650nm)."""
        R_blue = float(self.lut_co.R_atm[1, 0, 0])   # AOD=0.2, 450 nm
        R_red  = float(self.lut_co.R_atm[1, 0, 2])   # AOD=0.2, 650 nm
        self.assertGreater(
            R_blue, R_red,
            msg=f"R_atm continental: 450nm={R_blue:.4f} ≤ 650nm={R_red:.4f}",
        )


class TestLutGeometrySensitivity(TestCase):
    """Tests that LUT values respond physically to viewing geometry changes."""

    @classmethod
    def setUpClass(cls):
        cls.cfg_lo, cls.lut_lo = _make_lut(sza=20.0)
        cls.cfg_hi, cls.lut_hi = _make_lut(sza=60.0)

    def test_higher_sza_increases_R_atm(self):
        """R_atm at 450 nm must be larger for SZA=60° than SZA=20°."""
        R_lo = float(self.lut_lo.R_atm[1, 0, 0])  # AOD=0.2, H2O=1.0, 450 nm
        R_hi = float(self.lut_hi.R_atm[1, 0, 0])
        self.assertGreater(
            R_hi, R_lo,
            msg=f"R_atm(450nm): SZA=60°={R_hi:.4f} ≤ SZA=20°={R_lo:.4f}",
        )

    def test_higher_sza_decreases_T_total(self):
        """T_down×T_up at 650 nm must decrease for SZA=60° vs SZA=20°.

        650 nm is chosen because aerosol+Rayleigh extinction is strong enough
        there that the SZA effect is measurable; 550 nm and 450 nm may show
        partial compensation from enhanced diffuse transmittance.
        """
        T_lo = float(self.lut_lo.T_down[1, 0, 2] * self.lut_lo.T_up[1, 0, 2])
        T_hi = float(self.lut_hi.T_down[1, 0, 2] * self.lut_hi.T_up[1, 0, 2])
        self.assertLess(
            T_hi, T_lo,
            msg=f"T_total(650nm): SZA=60°={T_hi:.4f} ≥ SZA=20°={T_lo:.4f}",
        )

    def test_nadir_vs_oblique_T_up(self):
        """T_up must be lower for oblique VZA=50° than for nadir VZA=0°."""
        _, lut_nadir   = _make_lut(vza=0.0)
        _, lut_oblique = _make_lut(vza=50.0)
        T_nadir   = float(lut_nadir.T_up[1, 0, 1])    # AOD=0.2, 550 nm
        T_oblique = float(lut_oblique.T_up[1, 0, 1])
        self.assertLess(
            T_oblique, T_nadir,
            msg=f"T_up(550nm): VZA=50°={T_oblique:.4f} ≥ VZA=0°={T_nadir:.4f}",
        )


class TestLutH2OSensitivity(TestCase):
    """Tests for H₂O column influence on transmittances at 940 nm."""

    # Grid including 940 nm (H2O absorption) and 550 nm (transparent window)
    _WL_H2O = np.array([0.55, 0.87, 0.94, 1.02], dtype=np.float32)
    _H2O_RANGE = np.array([0.5, 1.0, 2.0, 4.0], dtype=np.float32)

    @classmethod
    def setUpClass(cls):
        cfg = ac.LutConfig(**{
            **_BASE_CFG,
            "wl":  cls._WL_H2O,
            "h2o": cls._H2O_RANGE,
        })
        cls.lut = ac.compute_lut(cfg)

    def test_T_down_decreases_with_h2o_at_940nm(self):
        """T_down at 940 nm must decrease monotonically with column H₂O."""
        T_940 = self.lut.T_down[0, :, 2]   # AOD=0, all H2O, wl=940 nm
        for k in range(len(self._H2O_RANGE) - 1):
            self.assertLessEqual(
                T_940[k + 1], T_940[k] + 1e-4,
                msg=(
                    f"T_down(940nm) increased from H2O={self._H2O_RANGE[k]:.1f} "
                    f"to {self._H2O_RANGE[k+1]:.1f}: "
                    f"{T_940[k]:.4f} → {T_940[k+1]:.4f}"
                ),
            )

    def test_T_down_nearly_constant_at_green_with_h2o(self):
        """T_down at 550 nm must vary < 2% across the full H₂O range."""
        T_550_lo = float(self.lut.T_down[0, 0, 0])   # H2O=0.5 g/cm²
        T_550_hi = float(self.lut.T_down[0, -1, 0])  # H2O=4.0 g/cm²
        np.testing.assert_allclose(
            T_550_hi, T_550_lo, rtol=0.02,
            err_msg=f"T_down(550nm) varies >2% with H2O: {T_550_lo:.4f}→{T_550_hi:.4f}",
        )

    def test_h2o_effect_larger_at_940_than_550(self):
        """H₂O sensitivity must be stronger at 940 nm than at 550 nm."""
        delta_940 = abs(float(self.lut.T_down[0, 0, 2]) - float(self.lut.T_down[0, -1, 2]))
        delta_550 = abs(float(self.lut.T_down[0, 0, 0]) - float(self.lut.T_down[0, -1, 0]))
        self.assertGreater(
            delta_940, delta_550,
            msg=f"ΔT_down(940nm)={delta_940:.4f} ≤ ΔT_down(550nm)={delta_550:.4f}",
        )


class TestPolarization(TestCase):
    """Tests for Stokes I,Q,U polarized RT (enable_polar=1)."""

    @classmethod
    def setUpClass(cls):
        cls.cfg_s, cls.lut_s = _make_lut(enable_polar=0)  # scalar
        cls.cfg_p, cls.lut_p = _make_lut(enable_polar=1)  # polarized

    def test_scalar_QU_are_none(self):
        """Scalar RT must return R_atmQ = R_atmU = None."""
        self.assertIsNone(self.lut_s.R_atmQ)
        self.assertIsNone(self.lut_s.R_atmU)

    def test_polar_QU_not_none(self):
        """Polarized RT must return non-None R_atmQ and R_atmU."""
        self.assertIsNotNone(self.lut_p.R_atmQ)
        self.assertIsNotNone(self.lut_p.R_atmU)

    def test_polar_QU_shape_matches_R_atm(self):
        """R_atmQ and R_atmU must have the same shape as R_atm."""
        expected = self.lut_p.R_atm.shape
        self.assertEqual(self.lut_p.R_atmQ.shape, expected)
        self.assertEqual(self.lut_p.R_atmU.shape, expected)

    def test_polar_R_atm_geq_scalar_at_blue(self):
        """Vector R_atm ≥ scalar R_atm at 450 nm (Rayleigh polarization raises I)."""
        R_vec = self.lut_p.R_atm[:, :, 0]    # all AOD/H2O, wl=450nm
        R_sca = self.lut_s.R_atm[:, :, 0]
        self.assertTrue(
            np.all(R_vec >= R_sca - 1e-4),
            msg=f"R_atm(polar) < R_atm(scalar) at 450 nm; max diff = {(R_sca - R_vec).max():.4f}",
        )

    def test_polar_Q_positive_at_blue(self):
        """R_atmQ > 0 at 450 nm for backscatter geometry (Rayleigh dominates)."""
        Q_blue = float(self.lut_p.R_atmQ[0, 0, 0])  # low AOD, H2O=1.0
        self.assertGreater(
            Q_blue, 0.0,
            msg=f"R_atmQ = {Q_blue:.4f} ≤ 0 at 450 nm (expected positive from Rayleigh)",
        )

    def test_polar_blue_improvement_1_to_10_pct(self):
        """Polarization improvement at 450 nm must be 1–10% of scalar R_atm."""
        R_vec = float(self.lut_p.R_atm[0, 0, 0])
        R_sca = float(self.lut_s.R_atm[0, 0, 0])
        if R_sca > 0:
            pct = 100.0 * (R_vec - R_sca) / R_sca
            self.assertGreater(pct, 1.0, msg=f"Polarization correction {pct:.2f}% < 1%")
            self.assertLess(pct, 10.0, msg=f"Polarization correction {pct:.2f}% > 10%")

    def test_polar_effect_decreases_from_blue_to_nir(self):
        """Polarization effect at 450 nm must be larger than at 870 nm."""
        diff_blue = float(self.lut_p.R_atm[0, 0, 0] - self.lut_s.R_atm[0, 0, 0])
        diff_nir  = float(self.lut_p.R_atm[0, 0, -1] - self.lut_s.R_atm[0, 0, -1])
        self.assertGreaterEqual(
            diff_blue, diff_nir,
            msg=(
                f"Polarization effect at 450nm ({diff_blue:.4f}) "
                f"< effect at 870nm ({diff_nir:.4f})"
            ),
        )


if __name__ == "__main__":
    test()
